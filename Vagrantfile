# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  config.vm.box = "debian/jessie64"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 2
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
  end

  # forward teh ssh-agent
  config.ssh.forward_agent = true

  # basic configuration
  config.vm.provision "shell", inline: <<-SHELL
    sudo apt-get update
    sudo apt-get install -y \
      git \
      vim \
      build-essential
  SHELL

  # setup git
  git_user_name = `git config user.name`.strip
  git_user_email = `git config user.email`.strip
  config.vm.provision "shell", privileged: false, inline: <<-EOF
    git config --global user.name "#{git_user_name}"
    git_name=$(git config --global user.name)
    git config --global user.email "#{git_user_email}"
    git_email=$(git config --global user.email)
    echo "git configured: ${git_name}, ${git_email}"
  EOF
end
