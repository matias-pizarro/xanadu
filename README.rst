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

.. deploy variables safely. The playbooks expect them to be stored in ../../ansible_variables

.. create droplet01
ansible-playbook --extra-vars "droplet_name=droplet01" create_droplet.yml

.. apply configs to Digital Ocean hosts
cd ansible && ansible-playbook --extra-vars "hostname=droplet01.docbase.net" digital_ocean.yml