#!/bin/bash

if [ -z "$ENV_FILE" ]; then
    ENV_FILE="./env.list"
fi
echo "Using ENV file: $ENV_FILE"

. $ENV_FILE

POSIX_MNT="${MAPR_MOUNT_PATH}/${MAPR_CLUSTER}"
POSIX_VOL="${POSIX_MNT}${MAPR_STREAMS_VOLUME_LOCATION}"
POSIX_STREAM="${POSIX_MNT}${MAPR_STREAMS_STREAM_LOCATION}"

if [ -d ./conf ]; then
    CONF=1
else
    CONF=0
fi
# First check if a volume/directly exists, if not create a volume
if [ ! -d "$POSIX_VOL" ]; then
    echo "Volume not detected at $POSIX_VOL: Creating"
    $MAPRCLI volume create -path $MAPR_STREAMS_VOLUME_LOCATION -rootdirperms 775 -user "${MAPR_CONTAINER_USER}:fc,a,dump,restore,m,d mapr:fc,a,dump,restore,m,d" -ae $MAPR_CONTAINER_USER -name "$MAPR_STREAMS_VOLUME_NAME"

    if [ "$?" == "0" ]; then
        echo "Volume Created successfully"
    else
        echo "Volume Creation failed: Exiting"
        exit 1
    fi
else
    echo "Volume already exists"
fi

echo ""
# Check for the stream, if not create it using the security in the env.list file. 
if [ ! -L "$POSIX_STREAM" ]; then
    echo "Stream not detected at $POSIX_STREAM: Creating"
    $MAPRCLI stream create -path $MAPR_STREAMS_STREAM_LOCATION -defaultpartitions $MAPR_STREAMS_DEFAULT_PARTITIONS -ttl $MAPR_STREAMS_DEFAULT_TTL -produceperm "\(u:mapr\|g:$MAPR_CONTAINER_GROUP\|u:$MAPR_CONTAINER_USER\)" -consumeperm "\(u:mapr\|g:$MAPR_CONTAINER_GROUP\|u:$MAPR_CONTAINER_USER\)" -topicperm "\(u:mapr\|g:$MAPR_CONTAINER_GROUP\|u:$MAPR_CONTAINER_USER\)" -adminperm "\(u:mapr\|g:$MAPR_CONTAINER_GROUP\|u:$MAPR_CONTAINER_USER\)"
    if [ "$?" == "0" ]; then
        echo "Stream Created Successfully"
        echo "Creating Topic"
        for T in $MAPR_STREAMS_TOPICS; do
            echo ""
            echo "Creating Topic $T"
            $MAPRCLI stream topic create -path $MAPR_STREAMS_STREAM_LOCATION -topic $T
        done
    else
        echo "Stream Creation failed"
    fi
else
    echo "Stream location already exists"
fi

if [ -d ./conf ] && [ "$CONF" == "0" ]; then
    rm -rf ./conf
fi
