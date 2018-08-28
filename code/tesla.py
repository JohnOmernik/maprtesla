#!/usr/bin/python3

import json
import os
import sys
import time
import requests
import pprint
from collections import OrderedDict

import confluent_kafka
from confluent_kafka import Producer, KafkaError, version, libversion
import random


try:
    token_file = os.environ["TESLA_TOKEN_FILE"].replace('"', '')
except:
    print("You must provide a TESLA_TOKEN_FILE location that is writable")
    sys.exit(1)

try:
    creds_file = os.environ["TESLA_CREDS_FILE"].replace('"', '')
except:
    print("You must provide a TESLA_CREDS_FILE that contains your Tesla authentication")
    sys.exit(1)

try:
    carname = os.environ["TESLA_CARNAME"].replace('"', '')
except:
    print("You must provide a TESLA_CARNAME for us to work with")
    sys.exit(1)

try:
    refresh_secs = int(os.environ["TESLA_REFRESH_SECS"].replace('"', ''))
except:
    print("TESLA_REFRESH_SECS has not been set, using a default of: 50000")
    refresh_secs = 50000

try:
    data_secs = int(os.environ["TESLA_FULL_DATA_SECS"].replace('"', ''))
except:
    print("Full data refresh interval not provided, using default of 120 seconds")
    data_secs = 120

try:
    http_timeout = int(os.environ["TESLA_HTTP_TIMEOUT_SECS"].replace('"', ''))
except:
    print("Tesla HTTP timeout not provided, setting to 30 second default")
    http_timeout = 30

try:
    stdout_interval = int(os.environ["TESLA_STDOUT_INTERVAL"].replace('"', ''))
except:
    print("Tesla STDOUT_INTERVAL not provided, defauling to 30 minutes (1800 secs)")
    stdout_interval = 1800

last_data = 0

def main():

    print("Confluent Kafka Version: %s - Libversion: %s" % (version(), libversion()))
    topic_full =  os.environ["MAPR_STREAMS_STREAM_LOCATION"].replace('"', '') + ":" + os.environ["MAPR_STREAMS_TESLA_FULL_TOPIC"].replace('"', '')
    topic_stream =  os.environ["MAPR_STREAMS_STREAM_LOCATION"].replace('"', '') + ":" + os.environ["MAPR_STREAMS_TESLA_STREAM_TOPIC"].replace('"', '')

    print("Producing full messages to: %s" % topic_full)
    print("Producing stream messages to: %s" % topic_stream)
    p = Producer({'bootstrap.servers': ''})

    # Listen for messages
    running = True
    lastflush = 0

    app_auth = getAppAuth()
    token = loadToken(app_auth)
    vehicles = loadVehicleInfo(token)
    vehicle = None
    for v in vehicles['response']:
        if v['display_name'] == carname:
            vehicle = v
            break
    if vehicle is None:
        print("Could not find %s in vehicle list" % carname)
        sys.exit(1)

    all_data = loadData(token, vehicle['id'])['response']

    stream_items = ['speed', 'odometer', 'soc', 'elevation', 'est_heading', 'est_lat', 'est_lng', 'power', 'shift_state', 'native_type', 'heading', 'native_latitude', 'native_longitude']
    stream_string = ",".join(stream_items)

    output_items = ['timestamp'] + stream_items
    stream_url = "https://streaming.vn.teslamotors.com/stream/%s/?values=%s"  % (vehicle['vehicle_id'], stream_string)


    tokenidx = 0
    last_stream_line = ""
    last_all_data = False

    while running:
        curtime = int(time.time())
        if curtime - last_data > data_secs:
            try:
                all_data = loadData(token, vehicle['id'])['response']
                if all_data is None:
                    last_all_data = False
                    print("%s - all_data is None, going to slowly try to refresh this to correct" % curtime)
                    while all_data is None:
                        all_data = loadData(token, vehicle['id'])['response']
                        if all_data is None:
                            sleep(5)
                else:
                    if last_all_data == False:
                        print("%s - all_data success on new start or after previous failure" % curtime)
                    last_all_data = True
                produceMessage(p, topic_full, json.dumps(all_data))
                if curtime % stdout_interval == 0:
                    print("%s - logging at stdout interval - success" % curtime)
            except:
                print("%s - All Data load failure" % curtime)
        try:
            stream_resp = requests.get(stream_url, auth=(token['uname'], all_data['tokens'][tokenidx]), stream=True, timeout=http_timeout)
            
            for line in stream_resp.iter_lines():
                curtime = int(time.time())
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.find("Can't validate password") >= 0:
                        all_data = loadData(token, vehicle['id'])['response']
                        print("%s - Bad password - Refreshing Tokens" % curtime)
                        time.sleep(2)
                    elif last_stream_line != decoded_line:
                        dline = decoded_line.split(",")
                        myrec = OrderedDict(zip(output_items, dline))
                        produceMessage(p, topic_stream, json.dumps(myrec))
                        if curtime % stdout_interval == 0:
                            print("%s - Streaming well - success on stdout_interval" % curtime)
                        myrec = None
                        last_stream_line = decoded_line
                if int(time.time()) - last_data > data_secs:
                    try:
                        all_data = loadData(token, vehicle['id'])['response']
                        last_all_data = True
                        produceMessage(p, topic_full, json.dumps(all_data))
                    except:
                        last_all_data = False
                        break
        except requests.exceptions.ConnectionError:
            pass
        except:
            pass



def produceMessage(p, topic, message_json):
    
    try:
        p.produce(topic, value=message_json, callback=delivery_callback)
        p.poll(0)
    except BufferError as e:
        print("Buffer full, waiting for free space on the queue")
        p.poll(10)
        p.produce(topic, value=message_json,callback=delivery_callback)
    except KeyboardInterrupt:
        print("\n\nExiting per User Request")
        p.close()
        sys.exit(0)

def delivery_callback(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed to %s failed: %s' % (msg.topic(), err))
    else:
        pass

def getAppAuth():
    resp = requests.get('https://pastebin.com/raw/YiLPDggh')
    raw = str(resp.text)
    client_data = json.loads('{' + raw.rstrip(',') + '}')
    return client_data

def getToken(app_auth, uname, pword):
    rdata = {}
    rdata['client_id'] = app_auth['OWNERAPI_CLIENT_ID']
    rdata['client_secret'] = app_auth['OWNERAPI_CLIENT_SECRET']
    rdata['grant_type'] = 'password'
    rdata['email'] = uname
    rdata['password'] = pword

    resp = requests.post("https://owner-api.teslamotors.com/oauth/token", data=rdata)
    try:
        newtoken = json.loads(resp.text)
    except:
        print("no worikie")
        print(resp.text)
        sys.exit(1)
    newtoken['uname'] = uname
    writeToken(newtoken, token_file)
    return newtoken

def refreshToken(app_auth, token):
    rdata = {}
    rdata['client_id'] = app_auth['OWNERAPI_CLIENT_ID']
    rdata['client_secret'] = app_auth['OWNERAPI_CLIENT_SECRET']
    rdata['grant_type'] = 'refresh_token'
    rdata['refresh_token'] = token['refresh_token']

    resp = requests.post("https://owner-api.teslamotors.com/oauth/token", data=rdata)

    newtoken = json.loads(resp.text)
    newtoken['uname'] = token['uname']
    writeToken(newtoken, token_file)
    return newtoken

def loadCredsorToken(opfile):
    o = open(opfile, 'r')
    u = o.read()
    o.close
    creds = json.loads(u)
    return creds

def writeToken(token, token_file):

    o = open(token_file, 'w')
    o.write(json.dumps(token))
    o.close()
    os.chmod(token_file, 0o660)
    print("Token written")


def checkRefresh(app_auth, token):
        curtime = int(time.time())
        token_exp_time = token['created_at'] + token['expires_in']
        remaining_time = token_exp_time - curtime
        print("Token Created: %s - Token expires: %s - Cur Time: %s - Diff: %s" % (token['created_at'], token_exp_time, curtime, remaining_time))
        if remaining_time <= 0:
            print("Token Expired, Creating new token")
            os.remove(token_file)
            token = loadToken(app_auth)
        elif remaining_time < refresh_secs:
            print("Remaining time of %s is less than refresh interval of %s seconds: refreshing token" % (remaining_time, refresh_secs))
            mytoken = refreshToken(app_auth, token)
        else:
            mytoken = token
        return mytoken

def loadToken(app_auth):
    if os.path.isfile(token_file):
        print("Token found - loading")
        token = loadCredsorToken(token_file)
        token = checkRefresh(app_auth, token)
    else:
        print("Token not found, trying creds file at %s" % creds_file)
        if os.path.isfile(creds_file):
            creds = loadCredsorToken(creds_file)
            token = getToken(app_auth, creds['uname'], creds['pword'])
            creds = ""
        else:
            print("No token_file at %s or creds_file at %s found - Exiting" % (token_file, creds_file))
            sys.exit(1)
    return token




def apiRequest(url, token):
    headers = {}
    headers['Authorization'] = "Bearer %s" % token['access_token']
    resp = requests.get(url, headers=headers)
    return json.loads(resp.text, object_pairs_hook=OrderedDict)


def loadVehicleInfo(token):
    return apiRequest("https://owner-api.teslamotors.com/api/1/vehicles", token)

def loadVehicleState(token, vehicle_id):
    return apiRequest("https://owner-api.teslamotors.com/api/1/vehicles/%s/data_request/vehicle_state" % vehicle_id, token)

def loadChargeState(token, vehicle_id):
    return apiRequest("https://owner-api.teslamotors.com/api/1/vehicles/%s/data_request/charge_state" % vehicle_id, token)

def loadData(token, vehicle_id):
    global last_data
    last_data = int(time.time())
    return apiRequest("https://owner-api.teslamotors.com/api/1/vehicles/%s/data" % vehicle_id, token)




if __name__ == '__main__':
    main()
