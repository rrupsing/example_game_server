#!/bin/bash
MOB="mobile_server"
DJ="django_server"
PUPPET="puppet-3.2.2"

sudo apt-get update
sudo apt-get install rubygems
sudo apt-get install git
sudo gem install --no-rdoc --no-ri puppet-module
sudo gem install --no-rdoc --no-ri facter
sudo gem install --no-rdoc --no-ri hiera hiera-puppet

if [[ ! -d /var/www ]] ; then sudo mkdir /var/www; fi
if [[ ! -d /var/www/${MOB} ]] ; then sudo rm -rf /var/www/${MOB}; fi

sudo ln -s /home/ubuntu/${MOB} /var/www/${MOB}

# install puppet from source instead of through rubygems to get latest version (if it doesn't exist)
command -v puppet >/dev/null 2>&1 || {
    wget http://downloads.puppetlabs.com/puppet/${PUPPET}.tar.gz
    gzip -d -c ${PUPPET}.tar.gz | tar xf -
    cd ${PUPPET}
    sudo ruby install.rb
}

cd /etc/puppet/modules
sudo puppet module install puppetlabs/mysql
sudo puppet module install puppetlabs/stdlib 
sudo puppet module install puppetlabs/firewall
sudo puppet module install ripienaar/concat
sudo puppet module install thomasvandoren/redis
git clone https://github.com/puppetlabs/puppetlabs-apache.git apache
sudo cp -R /home/ubuntu/${MOB}/puppet/memcached /etc/puppet/modules

cd /home/ubuntu/${MOB}/puppet
sudo puppet apply webserver.pp --templatedir=/etc/puppet/templates
test="<VirtualHost *:80>\n DocumentRoot /var/www/${MOB}/${DJ}\nWSGIScriptAlias / /var/www/${MOB}/${DJ}/${DJ}/${DJ}.wsgi\nSetEnv DJANGO_SETTINGS_MODULE ${DJ}.settings\nPythonOption django.root /var/www/${MOB}/${DJ}\n</VirtualHost>"
sudo echo -e $test | sudo tee /etc/apache2/sites-enabled/25-$DJ.conf > /dev/null
cd /var/www/${MOB}/${DJ}
sudo python manage.py syncdb

# restart the apache server
sudo /etc/init.d/apache2 restart
