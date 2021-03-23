SET datestring=%date:~6,4%-%date:~3,2%-%date:~0,2%
.\simstack_src\release_tools\compiled_client.bat
rsync.exe -av %datestring%-simstack_linux.tar.gz nanodev:WordPress_SecureMode_01/nanomatch-files/software/simstack/current_release/
