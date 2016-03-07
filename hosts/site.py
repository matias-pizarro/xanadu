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
            jails_list = host.vars.get('jails', [])
            for jail_name in jails_list:
                hosts.append(jail_name)
        if len(hosts) > len(inventory.get_hosts()):
            return subprocess.check_output(["hosts/site.py", "flatlist", json.dumps(hosts)])
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
        jails_list = host.vars.get('jails', [])
        if len(jails_list):
            output['jail_hosts']['hosts'].append(host.name)
            host.vars['host_type'] = 'first_class'
            host.vars['loopback_if'] = host.vars.get('loopback_if', 'lo0')
            host.vars['jails_if'] = host.vars.get('jails_if', 'lo1')
            host.vars['jails_if_ipv4'] = host.vars.get('jails_if_ip', '10.0.x.y')
            host.vars['jails_if_ipv6'] = ':'.join(host.vars.get('ipv6')['address'].split(':')[0:-2] +['x', 'y'])
            for jail_name in jails_list:
                jail = inventory.get_host(jail_name)
                output['jails']['hosts'].append(jail.name)
                jail.vars['host_type'] = 'jail'
                jail.vars['jail_host'] = host.name
                jail.vars['hosting'] = host.vars.get('hosting', '')
                output['_meta']['hostvars'][jail.name] = jail.vars
        for feature in host.vars.get('features', []):
            host.vars['has_' + feature] = True
        output['_meta']['hostvars'][host.name] = host.vars
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
