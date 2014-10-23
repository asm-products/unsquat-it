# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu-server-12-10"
  config.vm.box_url = "http://puppet-vagrant-boxes.puppetlabs.com/ubuntu-server-10044-x64-vbox4210.box"

  # Forward MongoDB port
  config.vm.network :forwarded_port, guest: 27017, host: 50004
  config.vm.network :forwarded_port, guest: 8001, host: 8001

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider :virtualbox do |vb|
	vb.customize [
	  "modifyvm", :id,
	  "--memory", "512"
	]
  end

  config.vm.provision :puppet do |puppet|
	puppet.manifests_path = "./"
	# uncomment the line below if you add modules to puppet manifest
	# puppet.module_path    = "vagrant/puppet/modules"
	puppet.manifest_file  = "puppet.pp"
	puppet.options        = [
							  '--verbose',
							  #'--debug',
							]
  end
  
  # Run our app
  config.vm.provision :shell, path: "bootstrap.sh"
  
end
