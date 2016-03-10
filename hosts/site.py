#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import json
import os
import subprocess
import sys
import tempfile

from ansible.inventory import Inventory
from ansible.inventory.group import Group
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


def update_hosts(inventory, list_path):
    """First computes a list of hosts and their jails, assigning them to relevant group,
    then refreshes the inventory"""

    hosts = set()
    jail_hosts = set()
    jails = set()
    for host in inventory.get_hosts():
        hosts.update([host.name])
        if len(host.vars.get('jails', [])):
            jail_hosts.update([host.name])
            jails.update(host.vars.get('jails', []))
    hosts.update(jails)
    with open(list_path, 'ab') as host_list:
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


def update_features(inventory, list_path):
    features = collections.defaultdict(list)
    for host in inventory.get_hosts():
        for feature in host.vars.get('features', []):
            features[feature].append(host.name)
    with open(list_path, 'ab') as host_list:
        for feature, hosts in features.iteritems():
            host_list.write('\n[{}]\n{}'.format(feature, '\n'.join(hosts)))
    inventory.host_list = host_list.name
    inventory.refresh_inventory()


def update_vars(inventory):
    """Sets relevant variables"""

    jail_hosts = inventory.get_group('jail_hosts')
    for host in jail_hosts.get_hosts():
        jails_list = host.vars.get('jails', [])
        host.vars = combine_vars(host.get_group_vars(), host.vars)
        host.vars['is_first_class_host'] = True
        host.vars['is_jail'] = False
        host.vars['has_jails'] = len(jails_list) > 0
        set_features(inventory, host)
        set_packages(host)
        for jail_name in jails_list:
            jail = inventory.get_host(jail_name)
            jail.vars = combine_vars(jail.get_group_vars(), jail.vars)
            jail.vars['is_first_class_host'] = False
            jail.vars['is_jail'] = True
            jail.vars['jail_host'] = host.name
            jail.vars['hosting'] = host.vars.get('hosting', '')
            set_ips(host, jail)
            set_features(inventory, jail)
            set_packages(jail)


def get_group(inventory, group_name):
    if group_name in inventory.groups:
        group = inventory.get_group(group_name)
    else:
        group = Group(name=group_name)
        inventory.groups[group_name] = group
    return group


def set_features(inventory, host):
    for feature in host.vars.get('features', []):
        group = get_group(inventory, feature)
        group.add_host(host)
        host.vars['has_' + feature] = True


def set_packages(host):
    packages = set(host.vars.get('packages', []))
    for group in host.get_groups():
        packages.update(group.vars.get('packages', []))
    packages = list(packages)
    packages.sort()
    host.set_variable('packages', packages)


def set_ips(host, jail):
    ipv4_pattern = host.vars.get('jails_base_ipv4')
    ipv6_pattern = ':'.join(host.vars.get('ipv6')['address'].split(':')[0:-2] +['{type_idx}', '{jail_idx}'])
    type_idx = jail.vars['type_index'] = 1 if jail.vars['jail_type'] == 'service' else 2
    jail_idx = jail.vars['jail_index']
    port = str((type_idx + 3) * 1000 + jail_idx)
    type_idx = str(type_idx)
    jail_idx = str(jail_idx)
    jail.vars['ipv4'] = {
        'interface': host.vars['jails_if'],
        'address': ipv4_pattern.format(type_idx=type_idx, jail_idx=jail_idx),
        'netmask': host.vars['jails_ipv4_netmask'],
    }
    jail.vars['ipv6'] = {
        'interface': host.vars['jails_if'],
        'address': ipv6_pattern.format(type_idx=type_idx, jail_idx=jail_idx),
        'prefixlen': host.vars['jails_ipv6_prefixlen'],
    }
    jail.vars['ansible_ssh_port'] = port


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
    handle, list_path = tempfile.mkstemp(dir='./', text=True)
    update_hosts(inventory, list_path)
    update_features(inventory, list_path)
    os.remove(list_path)
    update_vars(inventory)
    # show_vars(inventory)

    output = json.dumps(output_dict(inventory))
    print(output)


if __name__ == "__main__":
    main()
