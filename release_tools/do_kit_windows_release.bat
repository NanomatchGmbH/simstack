SET datestring=%date:~6,4%-%date:~3,2%-%date:~0,2%

CALL .\simstack_src\release_tools\compiled_client.bat

echo "DONE BUILDING."
rsync %datestring%-simstack_windows.zip -avzh -e "ssh -F %USERPROFILE%\.ssh\config -i %USERPROFILE%\.ssh\id_rsa" nanodev:WordPress_SecureMode_01/nanomatch-files/software/simstack/current_release/
echo "RSYNC done"