#!/bin/bash

yes | sudo apt-get install build-essential python-dev python-setuptools

/etc/init.d/mongodb start

sudo easy_install pip

sudo /usr/local/bin/pip install -r /vagrant/requirements.txt

echo '#'
echo '#'
echo '# Woohoo! You did it!'
echo '# Now, type "vagrant ssh" to enter the VM'
echo '# Then, "python /vagrant/tornado_server.py" to start the app.'
echo '#'
echo '#'

#python /vagrant/tornado_server.py