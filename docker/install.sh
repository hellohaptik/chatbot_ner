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

# Get sample Nginx file for routing and GUI

cd /tmp
wget "https://s3-us-west-2.amazonaws.com/chatbotner/chatbot_ner_nginx/default"
bash -c "cat /tmp/default > /etc/nginx/sites-available/default"
rm -rf /etc/nginx/sites-enabled/default
ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
sed -i 's/www-data/root/g' /etc/nginx/nginx.conf
