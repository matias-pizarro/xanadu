.. create a virtual environment
mkvirtualenv --python=/usr/local/bin/python2 xanadu

.. install/update requirements
pip install --upgrade -r requirements.txt

.. store api-related info in environment variables
export DO_API_VERSION='2'
export DO_API_TOKEN='<YOUR_API_TOKEN_HERE>'

.. display Digital Ocean account details
./do_account.sh

.. display Digital Ocean options
./do_options.sh

.. retrieve required roles from Ansible Galaxy
ansible-galaxy install --server https://galaxy-qa.ansible.com -r requirements.yml

.. deploy variables safely.
.. symbolic link ansible/host_vars points to ../../ansible_variables/host_vars
.. this allows keeping sensitive values version-controlled in a separate repository


.. create an empty inventory file

.. create droplet01
ssh-keygen -f ~/.ssh/known_hosts -R droplet01.example.net
ansible-playbook --extra-vars "hostname=droplet01.example.net" create_droplet.yml

.. add droplet01.example.net to your inventory file
.. you can now access droplet01.example.net with 'ssh -A root@droplet01.example.net'

.. configure droplet01.example.net
ansible-playbook site.yml

.. create jail mail02.example.net on droplet01.example.net
ssh-keygen -f ~/.ssh/known_hosts -R [mail02.example.net]:4001
ansible-playbook --extra-vars "jail_host=droplet01.example.net jail=mail02.example.net" create_jail.yml

.. add mail02.example.net to your inventory file
.. you can now access mail02.example.net with 'ssh -Ap 4001 root@mail02.example.net'

.. configure all hosts, including jail mail02.example.net
ansible-playbook site.yml

.. run group when specifying tags
ansible-playbook --tags="group,openntpd" site.yml

.. You can dry-run a diffed playbook limited to a specific host
ansible-playbook site.yml --check --diff --limit droplet01.example.net
