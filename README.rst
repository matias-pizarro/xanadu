======
Xanadu
======


**a collection of Ansible playbooks to set-up basic but fully functional FreeBSD hosts and an ecosystem of service jails**

Free software: BSD license

    .. | PyPi: https://pypi.python.org/pypi/pybsd

    | Github: https://github.com/rebost/xanadu

    .. | Read the Docs: http://pybsd.readthedocs.org/

Installation
============

clone the repo: ::

   git clone git@github.com:rebost/xanadu.git && cd xanadu

or ::

    git clone https://github.com/rebost/xanadu.git && cd xanadu

create a virtual environment (presupposes `virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/>`_): ::

    mkvirtualenv --python=/usr/local/bin/python2 xanadu

install/update requirements: ::

    pip install --upgrade -r requirements.txt

retrieve required roles from Ansible Galaxy: ::

    ansible-galaxy install --server https://galaxy-qa.ansible.com -r requirements.yml

deploy variables safely and keep sensitive values version-controlled in a separate repository:

[see xanadu/examples/ansible_variables/ for an example of variables layout] ::

    cp -Rp examples/ansible_variables ../


Edit the ansible_variables files to reflect your hosts and use case

Deploy on Digital Ocean
=======================

store api-related info in environment variables: ::

    export DO_API_VERSION='2'
    export DO_API_TOKEN='<YOUR_API_TOKEN_HERE>'

display Digital Ocean account details: ::

    ./do_account.sh

display Digital Ocean options: ::

    ./do_options.sh

create droplet01:

[until our `merge request <https://github.com/ansible/ansible-modules-core/pull/2835>`_ is accepted,
comment the ipv6 parameter in `playbooks/roles/do_new_droplet/tasks/main.yml, l.14 <https://github.com/rebost/xanadu/tree/master/playbooks/roles/do_new_droplet/tasks/main.yml#L14>`_] ::

    ssh-keygen -f ~/.ssh/known_hosts -R droplet01.example.net
    ansible-playbook --extra-vars "hostname=droplet01.example.net" playbooks/create_droplet.yml

add droplet01.example.net to your inventory file: ::

   echo droplet01.example.net >> ../../ansible_variables/hosts

you can now access droplet01.example.net with: ::

    ssh -Ap 4001 root@droplet01.example.net

configure droplet01.example.net: ::

    ansible-playbook playbooks/site.yml

create jail mail02.example.net on droplet01.example.net: ::

    ssh-keygen -f ~/.ssh/known_hosts -R [mail02.example.net]:4001
    ansible-playbook --extra-vars "jail_host=droplet01.example.net jail=mail02.example.net" playbooks/create_jail.yml

add mail02.example.net to your inventory file: ::

   echo mail02.example.net >> ../../ansible_variables/hosts

you can now access mail02.example.net with: ::

    ssh -Ap 4001 root@mail02.example.net

configure all hosts, including jail mail02.example.net: ::

    ansible-playbook playbooks/site.yml

run group when specifying tags: ::

    ansible-playbook --tags="group,openntpd" site.yml

You can dry-run a diffed playbook limited to a specific host: ::

    ansible-playbook site.yml --check --diff --limit playbooks/droplet01.example.net
