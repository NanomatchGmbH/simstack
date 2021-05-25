#!/bin/bash

if [ ! -f "$1" ]
then
    echo "Please specify packed SimStack distribution as first argument."
    exit 1
fi
if [ ! -d "$2" ]
then
    echo "Please specify extra directory as second argument."
    exit 1

fi
SSD=$1
extradir="$2"

TODAY=$(date "+%F")

mkdir repack
cd repack
tar xf ../$1
mkdir simstack_linux
mv * simstack_linux
cp -r ../$2/* simstack_linux/
tar czf $TODAY-simstack_linux_configured.tar.gz simstack_linux
cd -
