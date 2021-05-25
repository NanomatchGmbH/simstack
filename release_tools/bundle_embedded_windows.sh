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
unzip ../$1
mkdir simstack_windows
mv * simstack_windows
cp -r ../$2/* simstack_windows/
zip -r $TODAY-simstack_windows_configured.zip simstack_windows
cd -
