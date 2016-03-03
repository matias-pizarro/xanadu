#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import subprocess
import sys

from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.vars.hostvars import HostVars

PLAYBOOK_PATH = './playbooks/site.yml'
STATIC_HOSTS_PATH = './hosts/static_hosts'
RUN = 1

if len(sys.argv) > 1 and sys.argv[1] == 'flatlist':
    RUN = 2

loader = DataLoader()
variable_manager = VariableManager()
variable_manager.get_vars(loader=loader)

inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=STATIC_HOSTS_PATH)
variable_manager.set_inventory(inventory)

if not os.path.exists(PLAYBOOK_PATH):
    print '[INFO] The playbook does not exist'
    sys.exit()

inventory.set_playbook_basedir(os.path.dirname(PLAYBOOK_PATH))

if RUN == 1:
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

    if len(jails['jails']['hosts']):
        jails = subprocess.check_output(["hosts/jails.py", "flatlist", json.dumps(jails)])
        print(jails)
else:
    jails = json.loads(sys.argv[2])
    for host, config in jails['_meta']['hostvars'].iteritems():
        # Do something
        pass
    print(json.dumps(jails))
