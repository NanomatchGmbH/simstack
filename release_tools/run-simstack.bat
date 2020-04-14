SETLOCAL ENABLEEXTENSIONS
SET me=%~n0
SET parent=%~dp0

IF EXIST "%parent%\anaconda3" GOTO RUN_SIMSTACK
echo "Running preinstall"
CALL "%parent%\install-simstack.bat"
:RUN_SIMSTACK
CALL "%parent%\anaconda3\condabin\conda.bat" activate base
python "%parent%\simstack\simstack"
