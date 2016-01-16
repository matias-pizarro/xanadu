.. display Digital Ocean options
./do_options.sh

.. create mail02 droplet
cd ansible && ansible-playbook create_mail02.yml

.. apply configs to Digital Ocean hosts
cd ansible && ansible-playbook digital_ocean.yml