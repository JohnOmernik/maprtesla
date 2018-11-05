#!/bin/bash


. ./env.list

PORTS=""

if [ "$MAPR_TICKETFILE_LOCATION" != "" ]; then
    echo "Setting Secure Cluster"
    VOLS="-v=${MAPR_TICKET_HOST_LOCATION}:${MAPR_TICKET_CONTAINER_LOCATION}:ro"
else
    VOLS=""
fi

# If the APP_CMD is blank OR a 1  is passed as an argument to run.sh run the conainter with /bin/bash
# This allows you to update the command in the container to start the app directly 
#if [ "$APP_CMD" == "" ] || [ "$1" == "1" ]; then
#    APP_RUN_CMD="/bin/bash"
#else
#    APP_RUN_CMD="/app/run/gorun.sh"
#fi


# Read the env.list and create the env.list.docker to use. 
env|sort|grep -P "^(MAPR_|APP_)" > ./env.list.docker

sudo docker run -it $PORTS $VOLS --env-file ./env.list.docker \
--device /dev/fuse \
--ipc host \
--cap-add SYS_ADMIN \
--cap-add SYS_RESOURCE \
--security-opt apparmor:unconfined \
 $APP_IMG 
