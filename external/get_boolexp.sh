#!/bin/bash
wget "https://pypi.python.org/packages/08/62/d2c0215982fe03ee35d0277e35af47c5f8aae1559038039a372c8f822eb8/boolexp-0.1.tar.gz#md5=999ee191454463ce864dc586431974a6"
tar xf boolexp-0.1.tar.gz 
mv boolexp-0.1/boolexp .
rm -r boolexp-0.1
rm boolexp-0.1.tar.gz

