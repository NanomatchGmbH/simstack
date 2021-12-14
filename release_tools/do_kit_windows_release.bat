SET datestring=%date:~6,4%-%date:~3,2%-%date:~0,2%

CALL .\simstack_src\release_tools\compiled_client.bat

echo "DONE BUILDING."
rsync %datestring%-simstack_windows.zip -avzh -e "ssh -F %USERPROFILE%\.ssh\config -i %USERPROFILE%\.ssh\id_rsa" www.simstack.de@ssh.strato.de:WordPress_SecureMode_01/nanomatch-files/software/simstack/
echo "nanomatch-files/software/simstack/%datestring%-simstack_windows.zip"
echo "Please add here: https://www.simstack.de/wp-admin/post.php?post=284&action=edit"
echo "RSYNC done"
