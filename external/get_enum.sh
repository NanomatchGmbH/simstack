#!/bin/bash
wget "https://pypi.python.org/packages/bf/3e/31d502c25302814a7c2f1d3959d2a3b3f78e509002ba91aea64993936876/enum34-1.1.6.tar.gz#md5=5f13a0841a61f7fc295c514490d120d0"
tar xf enum34-1.1.6.tar.gz
mv enum34-1.1.6/enum .
rm -r enum34-1.1.6 enum34-1.1.6.tar.gz
