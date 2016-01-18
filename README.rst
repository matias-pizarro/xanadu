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

.. create droplet01
cd ansible && ansible-playbook create_droplet01.yml

.. apply configs to Digital Ocean hosts
cd ansible && ansible-playbook digital_ocean.yml