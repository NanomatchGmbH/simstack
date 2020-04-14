SETLOCAL ENABLEEXTENSIONS
SET me=%~n0
SET parent=%~dp0

IF EXIST "%parent%\anaconda3" GOTO RUN_SIMSTACK
echo "Running preinstall"
"%parent%\install-simstack.bat"
:RUN_SIMSTACK
"%parent%\anaconda3\python.exe" "%parent%\simstack\simstack"
