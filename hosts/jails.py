#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import json
import os
import subprocess
import sys

from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.vars.hostvars import HostVars

PLAYBOOK_PATH = './playbooks/site.yml'
STATIC_HOSTS_PATH = './static_hosts'


def tree():
    return collections.defaultdict(tree)

def group():
    return collections.defaultdict(dict, {"hosts": []})

def state_of_the_union():
    """On the first run HOSTS_LIST resolves to the path containing all static
    hosts definitions. On the second run it contains the list of static hosts and their jails"""

    if len(sys.argv) > 1 and sys.argv[1] == 'flatlist':
        RUN = 2
        HOSTS_LIST = json.loads(sys.argv[2])
    else:
        RUN = 1
        HOSTS_LIST = STATIC_HOSTS_PATH
    return RUN, HOSTS_LIST


def first_run(inventory):
        """On first running this script extracts the list of jails from each host and calls itself
        again so that on the next run we can access both host and jail vars. If no jails are defined
        it exits."""
        hosts = []
        for host in inventory.get_hosts():
            hosts.append(host.name)
            host_vars = inventory.get_host_vars(host)
            jails_list = host_vars.get('jails', [])
            for jail_name in jails_list:
                hosts.append(jail_name)
        if len(hosts) > len(inventory.get_hosts()):
            return subprocess.check_output(["hosts/jails.py", "flatlist", json.dumps(hosts)])
        else:
            return "{}"


def second_run(inventory):
    """On its second run this script has access to both host and jail vars. Any suitable logic
    to programmatically parametrize jails can be inserted here."""
    output = {
        "jail_hosts": group(),
        "jails": group(),
        "_meta": {"hostvars": tree()}
    }

    for host in inventory.get_hosts():
        host_vars = inventory.get_host_vars(host)
        jails_list = host_vars.get('jails', [])
        if len(jails_list):
            output['jail_hosts']['hosts'].append(host.name)
            output['_meta']['hostvars'][host.name]['host_type'] = 'first_class'
            output['_meta']['hostvars'][host.name]['loopback_if'] = host_vars.get('loopback_if', 'lo0')
            output['_meta']['hostvars'][host.name]['jails_if'] = host_vars.get('jails_if', 'lo1')
            output['_meta']['hostvars'][host.name]['jails_if_ipv4'] = host_vars.get('jails_if_ip', '10.0.x.y')
            for jail_name in jails_list:
                jail = inventory.get_host(jail_name)
                jail_vars = inventory.get_host_vars(jail)
                output['jails']['hosts'].append(jail.name)
                output['_meta']['hostvars'][jail.name]['host_type'] = 'jail'
                output['_meta']['hostvars'][jail.name]['jail_host'] = host.name
                output['_meta']['hostvars'][jail.name]['hosting'] = host_vars.get('hosting', '')
        for feature in host_vars.get('features', []):
            output['_meta']['hostvars'][host.name]['has_' + feature] = True
    return json.dumps(output)


def main():
    RUN, HOSTS_LIST = state_of_the_union()

    loader = DataLoader()
    variable_manager = VariableManager()
    variable_manager.get_vars(loader=loader)

    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=HOSTS_LIST)
    variable_manager.set_inventory(inventory)

    if not os.path.exists(PLAYBOOK_PATH):
        print '[INFO] The playbook does not exist'
        sys.exit()

    inventory.set_playbook_basedir(os.path.dirname(PLAYBOOK_PATH))

    output = first_run(inventory) if RUN == 1 else second_run(inventory)
    print(output)


if __name__ == "__main__":
    main()
