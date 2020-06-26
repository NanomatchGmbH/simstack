#!/bin/bash

if [ ! -f "run-simstack.sh" ]
then
    echo "Please run this script in the main extracted binary simstack folder."
    exit 0
fi

mv simstack/ simstack_binary_backup_2del/
git clone --recursive ssh://git@gitlab.nanobuild.de:2222/nanomatch/simstack.git simstack

