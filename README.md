USV.com Tech Documentation
===========================

Setting up a development environment
-------------------------------------

1) Download and install [Vagrant](http://www.vagrantup.com/downloads.html)

2) Download and install [Virtualbox](https://www.virtualbox.org/wiki/Downloads)

3) Get the USV codebase: 

    mkdir usv.com
    cd usv.com
    git init
    git remote add gh-usv git@github.com:unionsquareventures/usv.com.git
    git pull gh-usv
    git checkout mongoengine
    
(mongoengine is the current development branch, which is configured to work with vagrant)

4) Setup your local settings file.  Create a file called `settings_local_environ.py` in the application root directory.  Copy & paste the values from [this template](https://docs.google.com/a/usv.com/document/d/1LPLB4H795VyP3TQ8MGKdlkPC3_TNaeUpKUrotQEJHbU/edit?usp=drive_web).

5) Build your vagrant VM & run the app:

    $ vagrant up

That should run for a few minutes, and result in something like:

    ==> default: INFO:root:starting tornado_server on 0.0.0.0:8001

6) Pull it up in your browser:

    http://localhost:8001

From there, you can make edits using your text editor of choice.  When you make edits to application files, the application will automatically restart.

To SSH into the server, you can do that with `vagrant ssh`.  That will bring you into the vagrant vm.  The app files are synced inside the vm, and are located in `/vagrant/`.

To restart the server (for example, when it pukes and stops b/c of a syntax or import error), run `$ python tornado_server.py`.


### Handy trick for keeping track of git branches:

in your `~/.bash_profile` file (make one if you don't already have one), add the following:

    function parse_git_branch () {
           git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
    }
    
    RED="\[\033[0;31m\]"
    YELLOW="\[\033[0;33m\]"
    GREEN="\[\033[0;32m\]"
    NO_COLOUR="\[\033[0m\]"

    PS1="$GREEN\u@machine$NO_COLOUR:\w$YELLOW\$(parse_git_branch)$NO_COLOUR\$ "

Save this file.  In any open terminal windows run `$ source ~/.bash_profile` to reset that window.  From now on, each terminal window will have a handy reminder of what branch you're currently working in.


Deployment
----------
* Deployment is done via Heroku: [id.heroku.com](http://id.heroku.com)
* __TODO:__ use [heroku pipelines](https://devcenter.heroku.com/articles/labs-pipelines) to create an organized staging ==> prod workflow.
* To work with heroku from the command line, install the [Heroku toolbelt](https://toolbelt.heroku.com/)
* Configuration settings for the app can be found by running `$ heroku config --app <app-name>` (where <app-name> is the heroku app ID -- "usv-prod" for production and "usv-dev" for dev)


Communication
-------------
* Use [__tech@usv.com__](mailto://tech@usv.com) to communicate about web/tech issues.  
* Send an email to tech@usv.com with an update after code pushes, with link to commit.
