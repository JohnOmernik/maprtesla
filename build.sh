#!/bin/bash

. ./env.list
MYDIR=$(pwd)

git clone https://github.com/$APP_GIT_USER/$APP_GIT_REPO
cd $APP_GIT_REPO
./build.sh
cd ..

