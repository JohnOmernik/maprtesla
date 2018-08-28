#!/usr/bin/python3

import json
import os
import sys
import time
import requests
import pprint
from collections import OrderedDict

token_file = "./token"
creds_file = "./creds"
out_stream = "./out_stream.json"
out_full = "./out_full.json"
refresh_secs = 50000
carname = "Soka"
last_data = 0
data_secs = 120
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

    newtoken = json.loads(resp.text)
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



def main():
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
#    vehicle_state = loadVehicleState(token, vehicle['id'])['response']
 #   charge_state = loadChargeState(token, vehicle['id'])['response']

    all_data = loadData(token, vehicle['id'])['response']

#    print(vehicle)


    stream_items = ['speed', 'odometer', 'soc', 'elevation', 'est_heading', 'est_lat', 'est_lng', 'power', 'shift_state', 'native_type', 'heading', 'native_latitude', 'native_longitude']
    stream_string = ",".join(stream_items)

    output_items = ['timestamp'] + stream_items
    stream_url = "https://streaming.vn.teslamotors.com/stream/%s/?values=%s"  % (vehicle['vehicle_id'], stream_string)


    tokenidx = 0
    last_stream_line = ""

    while 1 == 1:
        fh_stream = open(out_stream, "a")
        fh_full = open(out_full, "a")
        if int(time.time()) - last_data > data_secs:
            try:
                all_data = loadData(token, vehicle['id'])['response']
                if all_data is None:
                    print("all_data is None, going to slowly try to refresh this to correct")
                    while all_data is None:
                        all_data = loadData(token, vehicle['id'])['response']
                        if all_data is None:
                            sleep(5)
                fh_full.write(json.dumps(all_data) + "\n")
                pprint.pprint(all_data)
            except:
                print("All Data load failure")
        try:
            stream_resp = requests.get(stream_url, auth=(token['uname'], all_data['tokens'][tokenidx]), stream=True, timeout=30)
            for line in stream_resp.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.find("Can't validate password") >= 0:
                        all_data = loadData(token, vehicle['id'])['response']
                        print("Bad password - Refreshing Tokens")
                        time.sleep(2)
                    elif last_stream_line != decoded_line:
                        dline = decoded_line.split(",")
                        myrec = OrderedDict(zip(output_items, dline))
                        print(myrec)
                        fh_stream.write(json.dumps(myrec) + "\n")
                        myrec = None
                        last_stream_line = decoded_line
                if int(time.time()) - last_data > data_secs:
                    try:
                        all_data = loadData(token, vehicle['id'])['response']
                        fh_full.write(json.dumps(all_data) + "\n")
                        pprint.pprint(all_data)
                    except:
                        break
        except requests.exceptions.ConnectionError:
            pass
        fh_stream.close()
        fh_full.close() 




if __name__ == '__main__':
    main()
