#!/bin/bash
# Debian/Ubuntu
if [ -e  /etc/network/interfaces ]; then
  sudo apt-add-repository multiverse
  sudo apt-get update
  echo 'ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true' | sudo debconf-set-selections
  sudo apt-get install -y ubuntu-restricted-extras
  sudo apt-get install -y vim
  sudo apt-get install -y libdvdread4
  sudo /usr/share/doc/libdvdread4/install-css.sh
  sudo /sbin/ldconfig
  sudo apt-get install -y nfs-common
  sudo apt-get install -y vlc
  sudo apt-get install -y git
  sudo apt-get install -y ruby 
#  sudo apt-get install -y python-pip
  sudo apt-get install -y python3
  sudo apt-get install -y python3-pip
  git config --global user.email "mcclusk@gmail.com"
  git config --global user.name "Chris McCluskey"
  sudo pip3 install python-magic

###################
# Redhat/Centos
elif [ -e /etc/redhat-release ]; then
  sudo rpm -Uvh http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm 
  sudo rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-5.el7.nux.noarch.rpm
  #sudo rpm -Uvh http://pkgs.repoforge.org/rpmfor@scge-release/rpmforge-release-0.5.3-1.el7.rf.x86_64.rpm 
  sudo rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
  sudo yum install -y libdvdread libdvdcss
  sudo yum install -y vlc
  #sudo yum install --disableplugin=fastestmirror -y xv
  #sudo yum install --disableplugin=fastestmirror -y geeqie
  ##sudo yum install --enable-repo=rpmforge-extras -y bchunk 
  #sudo yum install --disableplugin=fastestmirror -y /lib/ld-linux.so.2
  #sudo yum install --disableplugin=fastestmirror -y glibc glibc-common glibc-utils
  #sudo rpm -Uvh http://he.fi/bchunk/bchunk-1.2.0-0.i386.rpm
  #sudo yum install --disableplugin=fastestmirror -y unrar
  #sudo yum install --disableplugin=fastestmirror -y p7zip
fi

sudo mkdir /mnt/tmp
sudo mkdir /mnt/tmp2
sudo mkdir /mnt/tmp3
