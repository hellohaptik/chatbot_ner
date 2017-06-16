#!/bin/bash
mkdir -p ~/model_lib
cd /tmp/
wget ftp://ftp.netbsd.org/pub/pkgsrc/distfiles/CRF++-0.58.tar.gz
tar -xzf CRF++-0.58.tar.gz -C ~/model_lib/
cd ~/model_lib/CRF++-0.58/
./configure
make
make install

echo "export LD_LIBRARY_PATH=/usr/local/lib" >> ~/.bashrc

cd python
python setup.py build
python setup.py install
