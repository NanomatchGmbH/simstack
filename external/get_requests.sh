#!/bin/bash
wget "https://pypi.python.org/packages/2e/ad/e627446492cc374c284e82381215dcd9a0a87c4f6e90e9789afefe6da0ad/requests-2.11.1.tar.gz#md5=ad5f9c47b5c5dfdb28363ad7546b0763"
tar xf requests-2.11.1.tar.gz 
mv requests-2.11.1/requests .
rm -r requests-2.11.1
rm requests-2.11.1.tar.gz

