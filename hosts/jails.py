#!/usr/bin/env python

import json
import os
import sys

from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.vars.hostvars import HostVars

playbook_path = './playbooks/site.yml'
static_hosts_path = './hosts/static_hosts'

loader = DataLoader()
variable_manager = VariableManager()
variable_manager.get_vars(loader=loader)

inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=static_hosts_path)
variable_manager.set_inventory(inventory)

if not os.path.exists(playbook_path):
    print '[INFO] The playbook does not exist'
    sys.exit()

inventory.set_playbook_basedir(os.path.dirname(playbook_path))

jails = {
    "jails": {
        "hosts": []
    },
    "_meta": {
       "hostvars" : {}
    }
}

for host in inventory.get_hosts():
    host_vars = inventory.get_host_vars(host)
    jails_list = host_vars.get('jails', [])
    if not isinstance(jails_list, list):
        jails_list = list(jails_list)
    for jail in jails_list:
        jails['jails']['hosts'].append(jail)
        jails['_meta']['hostvars'][jail] = {'jail_host': host.name, 'hosting': host_vars.get('hosting', '')}

print(json.dumps(jails))

