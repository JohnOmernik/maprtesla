#!/bin/bash

. ./env.list

MYDIR=$(pwd)
#CODEDIR="$MYDIR/code"
#SAFEDIR="$MYDIR/safe"
PORTS=""



if [ "$MAPR_TICKETFILE_LOCATION" != "" ]; then
    echo "Setting Secure Cluster"
    VOLS="-v=${MAPR_TICKET_HOST_LOCATION}:${MAPR_TICKET_CONTAINER_LOCATION}:ro"
else
    VOLS=""
fi

CMD="/bin/bash"

env|sort|grep -P "^(MAPR_|APP_|TESLA_)" > ./env.list.docker

sudo docker run -it $PORTS $VOLS --env-file ./env.list.docker \
--device /dev/fuse \
--ipc host \
--cap-add SYS_ADMIN \
--cap-add SYS_RESOURCE \
--security-opt apparmor:unconfined \
 $IMG $CMD







