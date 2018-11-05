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
echo "-------------------------------------------------------"
echo "Stream Volume Location: $MAPR_STREAMS_VOLUME_LOCATION"
echo "Stream Volume Name: $MAPR_STREAMS_VOLUME_NAME"
echo "Stream Location: $MAPR_STREAMS_STREAM_LOCATION"
echo "Stram Topic(s): $MAPR_STREAMS_TOPICS"
echo "-------------------------------------------------------"
echo  ""
read -e -p "Are you sure you want to delete the topic(s), streams, and volumes here? THIS CAN NOT BE UNDONE!!!! (Y/N): " -i "N" CHK

if [ "$CHK" != "Y" ]; then
    echo "You did not type Y therefore we will exit"
    exit 0
fi

echo ""
echo "Deleteing Stream: $MAPR_STREAMS_STREAM_LOCATION"
$MAPRCLI stream delete -path $MAPR_STREAMS_STREAM_LOCATION
echo ""
sleep 1

echo "Deleting volume: $MAPR_STREAMS_VOLUME_NAME at $MAPR_STREAMS_VOLUME_LOCATION"
$MAPRCLI volume remove -name $MAPR_STREAMS_VOLUME_NAME -cluster $MAPR_CLUSTER
echo ""

if [ -d ./conf ] && [ "$CONF" == "0" ]; then
    rm -rf ./conf
fi
