#!/bin/bash

if [ ! -f "$1" ]
then
    echo "Please specify packed SimStack distribution as first argument."
    exit 1
fi
SSD=$1

rm -f virtuallab.tar.gz
rm -rf repack/

cd virtuallab/
git-archive-all ../virtuallab.tar.gz
cd -

TODAY=$(date "+%F")

mkdir repack
cd repack
tar xf ../virtuallab.tar.gz
rm ../virtuallab.tar.gz
mv virtuallab/* .
tar xf ../$1
mkdir simstack_linux
mkdir -p config/NanoMatch
mv * simstack_linux
tar czf $TODAY-simstack_linux_with_vlab.tar.gz simstack_linux
cd -
