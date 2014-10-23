class apt_update {
  exec { "aptGetUpdate":
      command => "sudo apt-get update",
      path => ["/bin", "/usr/bin"]
  }
}
  
class mongodb {
  exec { "10genKeys":
    command => "sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10",
    path => ["/bin", "/usr/bin"],
    notify => Exec["aptGetUpdate"],
    unless => "apt-key list | grep 10gen"
  }
  
  file { "10gen.list":
    path => "/etc/apt/sources.list.d/10gen.list",
    ensure => file,
    content => "deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen",
    notify => Exec["10genKeys"]
  }
  
  package { "mongodb-10gen":
    ensure => present,
    require => [Exec["aptGetUpdate"],File["10gen.list"]]
  }
}

class othertools {

  package { "vim-common":
    ensure => latest,
    require => Exec["aptGetUpdate"]
  }
  
  package { "wget":
    ensure => present,
    require => Exec["aptGetUpdate"]
  }

}

include apt_update
include othertools
include mongodb