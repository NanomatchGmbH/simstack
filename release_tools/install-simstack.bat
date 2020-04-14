SETLOCAL ENABLEEXTENSIONS
SET me=%~n0
SET parent=%~dp0
echo "Unpacking embedded Anaconda interpreter for SimStack. This can take up to 10 minutes."
:: start /wait "" "%parent%\tools_win\Miniconda3-latest-Windows-x86_64.exe" /InstallationType=JustMe /RegisterPython=0 /S /D=%parent%\anaconda3
CALL "%parent%anaconda3\condabin\conda.bat" activate base
"%parent%anaconda3\scripts\conda.exe" install --offline "%parent%\tools_win\pkgs\bcrypt-3.1.7-py37h8055547_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\ca-certificates-2020.4.5.1-hecc5488_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\certifi-2020.4.5.1-py37hc8dfbb8_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\conda-4.8.3-py37hc8dfbb8_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\decorator-4.4.2-py_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\icu-64.2-he025d50_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\jinja2-2.11.2-pyh9f0ad1d_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\jpeg-9c-hfa6e2cd_1001.tar.bz2" ^
	"%parent%\tools_win\pkgs\libblas-3.8.0-7_h8933c1f_netlib.tar.bz2" ^
	"%parent%\tools_win\pkgs\libcblas-3.8.0-7_h8933c1f_netlib.tar.bz2" ^
	"%parent%\tools_win\pkgs\libclang-9.0.1-default_hf44288c_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\libiconv-1.15-hfa6e2cd_1006.tar.bz2" ^
	"%parent%\tools_win\pkgs\liblapack-3.8.0-7_h8933c1f_netlib.tar.bz2" ^
	"%parent%\tools_win\pkgs\libpng-1.6.37-hfe6a214_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\libsodium-1.0.17-h2fa13f4_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\libxml2-2.9.10-h9ce36c8_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\libxslt-1.1.33-heafd4d3_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\lxml-4.5.0-py37h7005714_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\m2w64-gcc-libgfortran-5.3.0-6.tar.bz2" ^
	"%parent%\tools_win\pkgs\m2w64-gcc-libs-5.3.0-7.tar.bz2" ^
	"%parent%\tools_win\pkgs\m2w64-gcc-libs-core-5.3.0-7.tar.bz2" ^
	"%parent%\tools_win\pkgs\m2w64-gmp-6.1.0-2.tar.bz2" ^
	"%parent%\tools_win\pkgs\m2w64-libwinpthread-git-5.0.0.4634.697f757-2.tar.bz2" ^
	"%parent%\tools_win\pkgs\markupsafe-1.1.1-py37h8055547_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\msgpack-python-1.0.0-py37heaa310e_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\msys2-conda-epoch-20160418-1.tar.bz2" ^
	"%parent%\tools_win\pkgs\networkx-2.4-py_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\nomkl-1.0-h5ca1d4c_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\numpy-1.18.1-py37h90d3380_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\openssl-1.1.1f-hfa6e2cd_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\paramiko-2.7.1-py37_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\pynacl-1.3.0-py37h2fa13f4_1001.tar.bz2" ^
	"%parent%\tools_win\pkgs\pyparsing-2.4.7-pyh9f0ad1d_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\pyqt-5.12.3-py37h6538335_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\python_abi-3.7-1_cp37m.tar.bz2" ^
	"%parent%\tools_win\pkgs\pyyaml-5.1.2-py37hfa6e2cd_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\pyzmq-19.0.0-py37h8c16cda_1.tar.bz2" ^
	"%parent%\tools_win\pkgs\qt.py-1.2.2-py_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\qt-5.12.5-h7ef1ec2_0.tar.bz2" ^
	"%parent%\tools_win\pkgs\sshtunnel-0.1.5-0.tar.bz2" ^
	"%parent%\tools_win\pkgs\zeromq-4.3.2-h6538335_2.tar.bz2" ^
	"%parent%\tools_win\pkgs\zlib-1.2.11-h2fa13f4_1006.tar.bz2" 				
echo "Done"


