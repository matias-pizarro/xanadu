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
    dynamic_inventory = FreeBSDInventory(inventory)
    for host in inventory.host_list:
        host = dynamic_inventory.add_host('droplet01.docbase.net')
    import ipdb; ipdb.set_trace()
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


class Host(object):

    def __init__(self, inventory, name):
        self.inventory = inventory
        self.static_host = self.inventory.static_inventory.get_host(name)
        self.static_vars = self.inventory.static_inventory.get_host_vars(self.static_host)
        self.vars = self.inventory.data['_meta']['hostvars'][name]

    def override(self, key, value):
        pass

    def reconcile(self, key, value):
        pass



class FreeBSDInventory(object):

    def __init__(self, static_inventory):

        # Inventory data
        self.hosts = tree()
        self.groups = tree()
        self.data = {"_meta": {"hostvars": tree()}}
        self.static_inventory = static_inventory
        self.build_inventory()


    def build_inventory(self):
        '''Build Ansible inventory'''
        pass


    def add_host(self, name):
        '''Build Ansible inventory'''
        host = Host(self, name)
        self.hosts[name] = host
        return host


    def output(self):
        '''Print Ansible inventory'''
        json_data = self.inventory

        # if self.args.pretty:
        #     print(json.dumps(json_data, sort_keys=True, indent=2))
        # else:
        #     print(json.dumps(json_data))
        print(json.dumps(json_data))


if __name__ == "__main__":
    main()
