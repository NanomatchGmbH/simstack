IF EXIST %CD%\anaconda3 GOTO RUN_SIMSTACK
echo "Running preinstall"
%CD%\install-simstack.bat
:RUN_SIMSTACK
%CD%\anaconda3\python.exe %CD%\simstack\simstack