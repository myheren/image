#!/bin/bash
#only for ubuntu & please make sure current work dir is "imgCache/deploy"
echo -----------------------------------------
echo check system is ubuntu and make sure current work dir is "imgCache/deploy"
echo check you are superuser
echo ----------------------------------------
echo -----------------------------------------
echo check for essential packages
echo ----------------------------------------
if [ ! -f CherryPy-3.2.2.tar.gz ] 
then { 
   echo "miss CherryPy-3.2.2.tar.gz"
   exit 0
	 } 
fi

if [ ! -f libevent-2.0.21-stable.tar.gz ] 
then { 
   echo "miss libevent-2.0.21-stable.tar.gz"
   exit 0
   } 
fi

if [ ! -f memcached-1.4.15.tar.gz ] 
then { 
   echo "miss memcached-1.4.15.tar.gz"
   exit 0
   } 
fi

if [ ! -f python-memcached-1.53.tar.gz ] 
then { 
   echo "miss python-memcached-1.53.tar.gz"
   exit 0
   } 
fi

if [ ! -f setuptools-1.1.7.tar.gz ] 
then { 
   echo "miss setuptools-1.1.7.tar.gz"
   exit 0
   } 
fi

if [ ! -f uwsgi-1.9.18.2.tar.gz ] 
then { 
   echo "miss uwsgi-1.9.18.2.tar.gz"
   exit 0
   } 
fi
echo --------------------------------------------
echo setup environment with python-dev
echo --------------------------------------------
apt-get update
apt-get -y install python-dev

echo --------------------------------------------
echo install setuptools-1.1.7
echo -------------------------------------------
tar xvzf setuptools-1.1.7.tar.gz
cd setuptools-1.1.7
python setup.py install
cd ..

echo --------------------------------------------
echo install cherrypy
echo -------------------------------------------
tar xvzf CherryPy-3.2.2.tar.gz
cd CherryPy-3.2.2
python setup.py install
cd ..

echo --------------------------------------------
echo install memcache
echo -------------------------------------------
tar xvzf libevent-2.0.21-stable.tar.gz
cd libevent-2.0.21-stable
./configure --prefix=/usr
make
make install
cd ..

tar xvzf memcached-1.4.15.tar.gz
cd memcached-1.4.15
./configure --with-libevent=/usr
make
make install
cd ..

tar xvzf python-memcached-1.53.tar.gz
cd python-memcached-1.53
python setup.py install
cd ..

/usr/local/bin/memcached -d -m 10 -u root -p 11211 -c 256 -P memcached.pid

echo --------------------------------------------
echo install uwsgi
echo -------------------------------------------
tar xvzf uwsgi-1.9.18.2.tar.gz
cd uwsgi-1.9.18.2
python setup.py install
cd ..

echo --------------------------------------------
echo install nginx
echo -------------------------------------------
apt-get -y install nginx
mkdir /root/web
sed -i "/root/c\
root /root/web;" default
cp -f default /etc/nginx/sites-enabled
service nginx restart


echo --------------------------------------------
echo build the execute path
echo -------------------------------------------
cp -f ../upload.py /root
uwsgi --http :8000 --wsgi-file /root/upload.py &

echo --------------------------------------------
echo set rc.local for rebooting
echo -------------------------------------------
cp -f rc.local /etc/rc.local
apt-get -y install chkconfig
chkconfig --add nginx
chkconfig nginx on

echo --------------------------------------------
echo optional: install test env with ruby
echo --------------------------------------------
#apt-get install curl libcurl3 libcurl3-gnutls libcurl4-openssl-dev
#gem install curb

echo ---------------------------------------------
echo Start the whole system
echo ---------------------------------------------
echo press any key to reboot
read prop
reboot

