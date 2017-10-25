#!/bin/bash

MYPWD=`pwd`
if [ ! -d simstack_src ]
then
    echo "This file has to be called in the parent directory of the simstack src"
    exit 0
fi

if [ ! -f $MYPWD/anaconda3/pkgs/cython-*.tar.bz2 ]
then
    $MYPWD/anaconda3/bin/conda install cython
fi

rm -rf compiled_client installer_package simstack

mkdir compiled_client

cd simstack_src

rm -rf build compile
$MYPWD/anaconda3/bin/python ./setup.py install --prefix=../compiled_client/
rm -rf build compile
cd external
rm -rf build compile
$MYPWD/anaconda3/bin/python ./setup_pyura.py install --prefix=../../compiled_client
rm -rf build compile
cd $MYPWD

mkdir installer_package
cp -r compiled_client/lib/python3.6/site-packages/* installer_package/
rm -rf compiled_client
cp -r simstack_src/WaNo/ctrl_img installer_package/WaNo/
cp -r simstack_src/WaNo/wano_img installer_package/WaNo/
cp -r simstack_src/WaNo/workflow_img installer_package/WaNo/
cp -r simstack_src/WaNo/Media installer_package/WaNo/
cp simstack_src/simstack installer_package
mkdir installer_package/external
cp -r simstack_src/external/boolexp installer_package/external
cp -r simstack_src/external/Qt.py installer_package/external
cp simstack_src/Logo.png installer_package/

if [ ! -d simstack ]
then
    mv installer_package/ simstack
fi

