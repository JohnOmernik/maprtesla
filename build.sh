#!/bin/bash

. ./env.list
MYDIR=$(pwd)

REPO="maprpaccstreams"
git clone https://github.com/johnomernik/$REPO
cd $REPO
sudo docker build -t $IMG .
cd ..

