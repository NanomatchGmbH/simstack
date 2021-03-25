rd /s /q compiled_client installer_package simstack

mkdir compiled_client
CALL anaconda3\condabin\conda.bat activate base

cd simstack_src

rd /s /q build compile
python setup.py install --prefix=..\compiled_client\

rd /s /q build compile

cd SimStackServer
python ..\release_tools\git_archive_all.py --prefix=SimStackServer\ ..\..\compiled_client\Lib\site-packages\SimStackServer.zip
cd  ..\..\compiled_client\Lib\site-packages
unzip.exe SimStackServer.zip
del SimStackServer.zip


cd ..
cd ..
cd ..
cd simstack_src

cd external\TreeWalker
python ..\..\release_tools\git_archive_all.py --prefix=external\treewalker\  ..\..\..\compiled_client\Lib\site-packages\TreeWalker.zip
cd  ..\..\..\compiled_client\Lib\site-packages
unzip.exe TreeWalker.zip
REM del TreeWalker.zip

cd ..
cd ..
cd ..

mkdir installer_package
xcopy compiled_client\Lib\site-packages\* installer_package /s
rd /s /q compiled_client
xcopy simstack_src\WaNo\ctrl_img installer_package\WaNo\ctrl_img\ /s
xcopy simstack_src\WaNo\wano_img installer_package\WaNo\wano_img\ /s
xcopy simstack_src\WaNo\workflow_img installer_package\WaNo\workflow_img\ /s
xcopy simstack_src\WaNo\Media installer_package\WaNo\Media\ /s
xcopy simstack_src\simstack installer_package /s
mkdir installer_package\external
xcopy simstack_src\external\boolexp installer_package\external\boolexp\ /s
xcopy simstack_src\external\Qt.py installer_package\external\ /s
xcopy simstack_src\Logo.png installer_package\ /s

ren installer_package simstack

SET datestring=%date:~6,4%-%date:~3,2%-%date:~0,2%
rd /s /q %datestring%-simstack_windows.zip
zip.exe -r %datestring%-simstack_windows.zip run-simstack.bat simstack simstack.desktop simstack.eula tools_win

echo "DONE building."
