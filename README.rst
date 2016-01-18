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