#!/bin/bash

TODAY=$(date "+%F")
./simstack_src/release_tools/compiled_client.sh
if [ -f $TODAY-simstack_linux.tar.gz ]
then
    #rsync -av $TODAY-simstack_linux.tar.gz nanodev:WordPress_SecureMode_01/nanomatch-files/software/simstack/current_release/
    rsync -av $TODAY-simstack_linux.tar.gz stack:WordPress_SecureMode_01/nanomatch-files/software/simstack/
    echo "nanomatch-files/software/simstack/$TODAY-simstack_linux.tar.gz"
    echo "Please add here: https://www.simstack.de/wp-admin/post.php?post=286&action=edit"
else
    echo "Could not find $TODAY-simstack_linux.tar.gz. Maybe something went wrong."
fi
