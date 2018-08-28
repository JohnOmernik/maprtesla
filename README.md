# maprtesla
A python script to read Tesla API data and push to MapR Streams


## Build

The python script I wrote is actually pretty straight forward using common modules. I included a second copy of the script that was my early work to just write to files.  This could also work with MapR-FS through the fuse client or NFS Server, however, I wanted to put the data on streams. 

The first step is to clone and build different repository of mine. https://github.com/johnomernik/maprpaccstreams  

This can all be done via a simple command in this repo:

```
./build.sh
```

Once this is build it should be tagged maprpaccstreams:latest and be ready to use!

## Configure
At this point you want to take the env.list.template and copy to env.list

```
cp env.list.template env.list
```

Now you should go through and update the variables in env.list.

It should be fairly easy to understand, I've listed the application specific variables below but other variables related to the back are explained here:

https://mapr.com/docs/home/AdvancedInstallation/RunningtheMapRPACC.html

### creds file
In the folder ./safe you will need a creds file to do this:

```
cp ./creds.template ./safe/creds
```

Then open the ./safe/creds file and put your Tesla Account login information in the uname and pword fields


### ENV Variables


Required Variables

TESLA_TOKEN_FILE                # This is the file we write the token we obtain from Tesla. It should allow you remove the creds after startup. Further testing is needed. It does not need to exist prior to starting

TESLA_CREDS_FILE                # This file should have a json object in it with your username (email) and password for your Tesla Account. 

TESLA_CARNAME                   # This is the car name you wish to pull data from 

MAPR_STREAMS_STREAM_LOCATION    # This is the Location to the MapR Seam  

MAPR_STREAMS_TESLA_FULL_TOPIC   # This is the topic to use for full data

MAPR_STREAMS_TESLA_STREAM_TOPIC # This is the topic to use for streaming data

Optional Variables

TESLA_FULL_DATA_SECS            # This is the interval to pull the full data (non-streaming) data from car (Defaults to 120 seconds)

TESLA_REFRESH_SECS              # This is the interval in which when the time remaining on the token is below, it will request a new token from Tesla. (Defaults to 50,000 seonds)

TESLA_HTTP_TIMEOUT_SECS         # This is the timeout we set on the streaming protocol. If we don't see data in this time, we reconnect. (Defaults to 30 seconds) 

TESLA_STDOUT_INTERVAL           # This is the interval where it prints a success message at (Just to let you know things are happening) it defaults to 1800 seconds (30 minutes)

