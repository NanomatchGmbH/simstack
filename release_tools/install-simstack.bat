echo "Unpacking embedded Anaconda interpreter for SimStack. This can take up to 10 minutes."
start /wait "" "%CD%\tools\Miniconda3-latest-Windows-x86_64.exe" /InstallationType=JustMe /RegisterPython=0 /S /D=%CD%\anaconda3
echo "Nearly done. Preparing ICU package"
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\icu-58.2-ha66f8fd_1.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\jinja2-2.10-py36h292fed1_0.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\jpeg-9b-hb83a4c4_2.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\libiconv-1.15-h1df5818_7.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\libpng-1.6.32-h140d38e_4.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\libxml2-2.9.4-h41ea7b2_6.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\libxslt-1.1.29-h0037b19_6.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\lxml-4.1.1-py36he0adb16_0.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\markupsafe-1.0-py36h0e26971_1.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\pyqt-5.6.0-py36hb5ed885_5.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\python-dateutil-2.6.1-py36h509ddcb_1.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\pyyaml-3.12-py36h1d1928f_1.tar.bz2
echo "Nearly done. Preparing QT package. This one takes a bit longer again."
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\qt-5.6.2-vc14h6f8c307_12.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\simplejson-3.12.0-py36h3a23abe_0.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\sip-4.18.1-py36h9c25514_2.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\sqlite-3.20.1-h9eeafa9_2.tar.bz2
"%CD%\anaconda3\scripts\conda.exe" install --offline tools\pkgs\zlib-1.2.11-h8395fce_2.tar.bz2
echo "Done"
exit /b 0
