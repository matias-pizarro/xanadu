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

Clone the repo: ::

   git clone git@github.com:rebost/xanadu.git && cd xanadu

*or* ::

    git clone https://github.com/rebost/xanadu.git && cd xanadu

Create a virtual environment (presupposes `virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/>`_): ::

    mkvirtualenv --python=/usr/local/bin/python2 xanadu

Install/update requirements: ::

    pip install --upgrade -r requirements.txt

Retrieve dependencies from Ansible Galaxy: ::

    ansible-galaxy install --server https://galaxy-qa.ansible.com -r requirements.yml

Deploy variables safely and keep sensitive values version-controlled in a separate repository:

[*see xanadu/examples/ansible_variables/ for an example of variables layout*] ::

    cp -Rp examples/ansible_variables ../


Edit the ansible_variables files to reflect your hosts and use case



Deploy on Digital Ocean
=======================

Store api-related info in environment variables: ::

    export DO_API_VERSION='2'
    export DO_API_TOKEN='<YOUR_API_TOKEN_HERE>'

Display Digital Ocean account details: ::

    ./do_account.sh

Display Digital Ocean options: ::

    ./do_options.sh



Apply playbooks to hosts and jails
==================================

Create droplet01:

[*until this* `merge request <https://github.com/ansible/ansible-modules-core/pull/2835>`_ *is accepted,
comment the ipv6 parameter in* `playbooks/roles/do_new_droplet/tasks/main.yml, l.14 <https://github.com/rebost/xanadu/tree/master/playbooks/roles/do_new_droplet/tasks/main.yml#L14>`_] ::

    ssh-keygen -f ~/.ssh/known_hosts -R droplet01.example.net
    ansible-playbook --extra-vars "hostname=droplet01.example.net" playbooks/create_droplet.yml

Add droplet01.example.net to your inventory file: ::

   echo droplet01.example.net >> ../../ansible_variables/hosts

You can now access droplet01.example.net with: ::

    ssh -Ap 123 root@droplet01.example.net

Configure droplet01.example.net: ::

    ansible-playbook playbooks/site.yml

Create jail mail02.example.net on droplet01.example.net: ::

    ssh-keygen -f ~/.ssh/known_hosts -R [mail02.example.net]:4001
    ansible-playbook --extra-vars "jail_host=droplet01.example.net jail=mail02.example.net" playbooks/create_jail.yml

Add mail02.example.net to your inventory file: ::

   echo mail02.example.net >> ../../ansible_variables/hosts

You can now access mail02.example.net with: ::

    ssh -Ap 4001 root@mail02.example.net

Configure all hosts, including jail mail02.example.net: ::

    ansible-playbook playbooks/site.yml

Remember to run **'group'** when specifying tags: ::

    ansible-playbook --tags="group,openntpd" site.yml

You can dry-run a diff'ed playbook limited to a specific host: ::

    ansible-playbook site.yml --check --diff --limit playbooks/droplet01.example.net

If you add the following config to your .ssh/config... ::

    cat << EOF >> ~/.ssh/config
    Host droplet01
      HostName droplet01.example.net
      Port 123
      User root
      ForwardAgent yes

    Host mail02
      HostName mail02.example.net
      Port 4001
      User root
      ForwardAgent yes
    EOF

    chmod 600 ~/.ssh/config

... you can simplify ssh access: ::

    ssh droplet01
    ssh mail02

**Agent forwarding should be enabled with caution** (`man ssh_config <https://www.freebsd.org/cgi/man.cgi?query=ssh_config&sektion=5&n=1>`_)
