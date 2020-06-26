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
xcopy simstack_src\Logo.png installer_package\ /s

ren installer_package simstack

