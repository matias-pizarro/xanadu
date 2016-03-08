#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import json
import os
import subprocess
import sys
import tempfile

from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.utils.vars import combine_vars
from ansible.vars import VariableManager
from ansible.vars.hostvars import HostVars

PLAYBOOK_PATH = './playbooks/site.yml'
STATIC_HOSTS_PATH = './static_hosts'


def get_hosts_list():
    if len(sys.argv) > 2 and sys.argv[1] == '--host_list':
        return sys.argv[2]
    else:
        return STATIC_HOSTS_PATH


def update(inventory):
    """First computes a list of hosts and their jails, assigning them to relevant group,
    then refreshes the inventory"""

    handle, path = tempfile.mkstemp(dir='./', text=True)
    with open(path, 'w') as host_list:
        jail_hosts = set()
        hosts = set()
        jails = set()
        for host in inventory.get_hosts():
            jail_hosts.update([host.name])
            hosts.update([host.name])
            jails.update(host.vars.get('jails', []))
        hosts.update(jails)
        for host in hosts:
            host_list.write(host + '\n')
        host_list.write('[jail_hosts]\n')
        for host in jail_hosts:
            host_list.write(host + '\n')
        host_list.write('[jails]\n')
        for host in jails:
            host_list.write(host + '\n')
        host_list.write('[freebsd:children]\njails\njail_hosts')
    inventory.host_list = host_list.name
    inventory.refresh_inventory()
    os.remove(path)


def set_vars(inventory):
    """Sets relevant variables"""

    jail_hosts = inventory.get_group('jail_hosts')
    for host in jail_hosts.hosts:
        jails_list = host.vars.get('jails', [])
        host.vars = combine_vars(host.get_group_vars(), host.vars)
        host.vars['is_first_class_host'] = True
        host.vars['is_jail'] = False
        host.vars['has_jails'] = len(jails_list) > 0
        host.vars['jails_if_ipv4'] = host.vars.get('lo_base_ip') + '.x.y'
        host.vars['jails_if_ipv6'] = ':'.join(host.vars.get('ipv6')['address'].split(':')[0:-2] +['x', 'y'])
        for jail_name in jails_list:
            jail = inventory.get_host(jail_name)
            jail.vars = combine_vars(jail.get_group_vars(), jail.vars)
            jail.vars['is_first_class_host'] = False
            jail.vars['is_jail'] = True
            jail.vars['jail_host'] = host.name
            jail.vars['hosting'] = host.vars.get('hosting', '')
        for feature in host.vars.get('features', []):
            host.vars['has_' + feature] = True


def output_dict(inventory):
    output = {"_meta": {"hostvars": {}}}
    for host in inventory.get_hosts():
        output['_meta']['hostvars'][host.name] = host.get_vars()
    for group in inventory.groups.values():
        if group.name not in ('all', 'ungrouped'):
            output[group.name] = {"hosts": [host.name for host in group.get_hosts()]}
    return output


def show_vars(inventory):
    for host in inventory.get_hosts():
        hostvars = combine_vars(host.get_group_vars(), host.vars)
        print(json.dumps(hostvars, sort_keys=True, indent=4, separators=(',', ': ')))


def main():
    hosts_list = get_hosts_list()

    loader = DataLoader()
    variable_manager = VariableManager()
    variable_manager.get_vars(loader=loader)

    inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=hosts_list)
    variable_manager.set_inventory(inventory)

    if not os.path.exists(PLAYBOOK_PATH):
        print '[INFO] The playbook does not exist'
        sys.exit()

    inventory.set_playbook_basedir(os.path.dirname(PLAYBOOK_PATH))
    update(inventory)
    set_vars(inventory)
    # show_vars(inventory)

    output = json.dumps(output_dict(inventory))
    print(output)


if __name__ == "__main__":
    main()
