#package { 'build-essential': ensure => installed; }
package { 'php5=5.3.10-1ubuntu3.6': ensure => installed; }
package { 'python2.7': ensure => installed; }
package { 'python-dev': ensure => installed; }
package { 'python-setuptools': ensure => installed; }
package { 'python-pip': ensure => installed; }
package { 'django': ensure => '1.5.1', provider => 'pip'; }
package { 'phpmyadmin': ensure => installed; }
package { 'libmysqlclient-dev' : ensure => installed; }
package { 'MySQL-python': ensure => "1.2.3", require => Package['libmysqlclient-dev'], provider => pip; }
package { 'php5-curl': ensure =>installed; }

include mysql
class { 'mysql::server' :
	config_hash => { 'root_password' => 'test',
			'etc_root_password' => 'True' },
}

mysql::db  {'puppettest':
	user => 'testuser',
	password => 'test',
	host =>'localhost',
	grant => ['all'],
}

include memcached
package { 'python-memcached': ensure => installed, provider => 'pip'; }
package {'django-redis': ensure => installed, provider => 'pip'; }

class { 'apache': }

apache::vhost { 'django_server':
       port    => '80',
       vhost_name => '127.0.0.1',
       logroot => '/var/log/apache2/django',
       scriptalias => '/var/www/mobile_server/django_server/django_server/django_server.wsgi',
       setenv => 'DJANGO_SETTINGS_MODULE django_server.settings',
       docroot => '/var/www/mobile_server/django_server/django_server',
       custom_fragment => 'PythonOption django.root /var/www/mobile_server/django_server'
}

class {'apache::mod::python': }
class {'apache::mod::wsgi': }

file_line { 'phpmyadmin include':
	path => '/etc/apache2/apache2.conf',
	line => 'Include /etc/phpmyadmin/apache.conf',
}

class { 'redis': version => '2.6.5',
    redis_port => '6900',
    redis_bind_address => '127.0.0.1',
    redis_password => 'test',
    redis_max_memory => '1gb', }



