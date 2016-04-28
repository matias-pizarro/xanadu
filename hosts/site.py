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

DEBUG = True if '--debug' in sys.argv or '-d' in sys.argv else False
PLAYBOOK_PATH = './playbooks/site.yml'
FIRST_CLASS_HOSTS_PATH = './first_class_hosts'


def get_hosts_list():
    """Returns the hosts list filename"""

    if len(sys.argv) > 2 and sys.argv[1] == '--host_list':
        return sys.argv[2]
    else:
        return FIRST_CLASS_HOSTS_PATH


def update_hosts(inventory, list_path):
    """First computes a list of hosts and their jails, assigning them to relevant groups,
    then refreshes the inventory"""

    # Group containing all hosts
    hosts = set()
    # Group containing full-fledged, bare-metal hosts
    first_class_hosts = set()
    # Group containing hosts that host (!) jails
    jail_hosts = set()
    # Group containing all jailed hosts
    jails = set()
    for host in inventory.get_hosts():
        hosts.update([host.name])
        if len(host.vars.get('jails', [])):
            jail_hosts.update([host.name])
            jails.update(host.vars.get('jails', []))
    first_class_hosts = hosts.copy()
    hosts.update(jails)
    with open(list_path, 'ab') as host_list:
        for host in hosts:
            host_list.write(host + '\n')
        host_list.write('[first_class_hosts]\n')
        for host in first_class_hosts:
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
    """Collects features across all hosts and create groups for each of them,
    Then refreshes the inventory so their variables are available"""

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
    """Sets relevant variables for each host and jail"""

    first_class_hosts = inventory.get_group('first_class_hosts')
    for host in first_class_hosts.get_hosts():
        jails_list = host.vars.get('jails', [])
        host.vars = combine_vars(host.get_group_vars(), host.vars)
        host.vars['is_first_class_host'] = True
        host.vars['is_jail'] = False
        host.vars['is_not_jail'] = True
        host.vars['has_jails'] = len(jails_list) > 0
        set_features(inventory, host)
        set_providers(inventory, host)
        set_packages(host)
        for jail_name in jails_list:
            jail = inventory.get_host(jail_name)
            jail.vars = combine_vars(jail.get_group_vars(), jail.vars)
            jail.vars['is_first_class_host'] = False
            jail.vars['is_jail'] = True
            jail.vars['is_not_jail'] = False
            jail.vars['jail_host'] = host.name
            jail.vars['hosting'] = host.vars.get('hosting', '')
            set_features(inventory, jail, jail_host=host)
            set_providers(inventory, jail, jail_host=host)
            set_ips(host, jail)
            set_packages(jail)
            set_root_pubkeys(jail)


def get_group(inventory, group_name):
    """(creates if necessary) and returns group corresponding to group_name"""

    if group_name in inventory.groups:
        group = inventory.get_group(group_name)
    else:
        group = Group(name=group_name)
        inventory.groups[group_name] = group
    return group


def set_ips(host, jail):
    """Computes a jail's ip configuration based on its host's properties"""

    type_idx = jail.vars['type_index'] = 1 if jail.vars['jail_type'] == 'service' else 2
    jail_idx = jail.vars['jail_index']
    port = str((type_idx + 3) * 1000 + jail_idx)
    type_idx = str(type_idx)
    jail_idx = str(jail_idx)
    ipv4_pattern = host.vars.get('jails_base_ipv4')
    host.vars['lo_base_ip'] = ipv4_pattern.format(type_idx=1, jail_idx=1)
    jail.vars['ext_if'] = {
        'name': host.vars['jails_if'],
        'ipv4s': [{
            'address': ipv4_pattern.format(type_idx=type_idx, jail_idx=jail_idx),
            'netmask': host.vars['jails_ipv4_netmask'],
        }],
        'ipv6s': []
    }
    if host.vars.get('has_ipv6', False):
        ipv6_pattern = ':'.join(host.vars['ext_if']['ipv6s'][0]['address'].split(':')[0:-2] +['{type_idx}', '{jail_idx}'])
        jail.vars['ext_if']['ipv6s'].append({
            'address': ipv6_pattern.format(type_idx=type_idx, jail_idx=jail_idx),
            'netmask': host.vars['jails_ipv6_netmask'],
        })
    if host.vars.get('has_vpn_host', False):
        vpn_ipv4_pattern = host.vars.get('vpn_base_ipv4')
        jail.vars['vpn_if'] = {
            'name': host.vars['vpn_if'],
            'address': vpn_ipv4_pattern.format(type_idx=type_idx, jail_idx=jail_idx),
            'netmask': host.vars['vpn_ipv4_netmask'],
        }
    jail.vars['ansible_ssh_port'] = port


def set_features(inventory, host, jail_host=None):
    """Assigns hosts groups based on their features. This allows hosts to inherit variables
    based on their features and gives plays feature-based flow control """

    for feature in host.vars.get('features', []):
        group = get_group(inventory, feature)
        group.add_host(host)
        host.vars['has_' + feature] = True


def set_providers(inventory, host, jail_host=None):
    """Assigns hosts variables based on services they or their child jails provide.
    This gives plays service-based flow control."""

    if 'providers' not in host.vars:
        host.vars['providers'] = {}
    if jail_host and 'providers' not in jail_host.vars:
        jail_host.vars['providers'] = {}
    provisions = []
    for provision in [group.vars['provides'] for group in host.get_groups() if 'provides' in group.vars]:
        provisions += provision
    for provision in provisions:
        host.vars['provides_' + provision] = True
        host.vars['providers'][provision] = host.name
        if jail_host:
            jail_host.vars['provides_' + provision] = True
            jail_host.vars['providers'][provision] = host.name


def set_packages(host):
    """Builds a list of packages for each host, based on their own packages and those defined
    for the groups they belong to"""

    packages = set(host.vars.get('packages', []))
    for group in host.get_groups():
        packages.update(group.vars.get('packages', []))
    packages = list(packages)
    packages.sort()
    host.set_variable('packages', packages)


def set_root_pubkeys(host):
    """Aggregates the hosts root user authorized keys into a string
    that can be used with the authorized_keys modules when creating a jail"""

    pubkeys = ""
    for pubkey in host.vars['users']['root']['pubkeys']:
        with open(os.path.join('playbooks/files', pubkey)) as pkf:
            pubkeys += pkf.read() + '\n'
    host.set_variable('root_pubkeys', pubkeys)


def update_variables(inventory):
    """Once all groups, features, providers etc... are set,
    set any and all variables that depend on these"""

    http_proxied = inventory.get_group('http_proxied')
    if http_proxied:
        proxied_sites = []
        proxy_configs = {}
        all_proxy_configs = ['default.conf']
        proxied_domains = {}
        proxied_jails = [host.vars['jail_name'] for host in http_proxied.get_hosts()]
        for host in http_proxied.get_hosts():
            proxy_configs[host.vars['hostname']] = ['default.conf']
            proxied_domains[host.vars['hostname']] = []
            for site in host.vars['sites']:
                proxied_domains[host.vars['hostname']] += site['fqdns'].split()
                proxy_configs[host.vars['hostname']].append('{}.conf'.format(site['name']))
                all_proxy_configs.append('{}.conf'.format(site['name']))
                site['jail'] = host.vars['hostname']
                site['jail_name'] = host.vars['jail_name']
                site['ipv4s'] = ' '.join([ipv4['address'] for ipv4 in host.vars['ext_if']['ipv4s']])  # should be vpn_ipv4 when vpn is set
                proxied_sites.append(site)
    jail_hosts = inventory.get_group('jail_hosts')
    for host in jail_hosts.get_hosts():
        host.set_variable('proxied_sites', proxied_domains)
        host.set_variable('proxy_configs', proxy_configs)
        host.set_variable('all_proxy_configs', all_proxy_configs)
        host.set_variable('proxied_domains', proxied_domains)
        if 'providers' in host.vars:
            jails_list = host.vars.get('jails', [])
            for jail_name in jails_list:
                jail = inventory.get_host(jail_name)
                jail.vars['providers'] = host.vars['providers']
                jail.set_variable('proxied_sites', proxied_sites)
                jail.set_variable('proxy_configs', proxy_configs)
                jail.set_variable('all_proxy_configs', all_proxy_configs)
                jail.set_variable('proxied_domains', proxied_domains)
                for provision, provider_name in host.vars['providers'].iteritems():
                    provider = inventory.get_host(provider_name)
                    if provider == host or provider.vars['jail_host'] == jail.vars['jail_host']:
                        jail.set_variable('{}_provider'.format(provision), provider.vars['ext_if']['ipv4s'][0]['address'])
                    else:
                        jail.set_variable('{}_provider'.format(provision), provider.vars['vpn_ipv4']['address'])

def ansible_output(inventory):
    """Groups inventory data according to the structure Ansible expects"""

    output = {'_meta': {'hostvars': {}}}
    for host in inventory.get_hosts():
        output['_meta']['hostvars'][host.name] = host.get_vars()
    for group in inventory.groups.values():
        if group.name not in ('all', 'ungrouped'):
            output[group.name] = {'hosts': [host.name for host in group.get_hosts()]}
    return json.dumps(output)


def debug_output(inventory):
    """Returns a json representation of inventory data, for debugging purposes"""

    output = {'hosts': {}, 'groups': {}}
    for host in sorted(inventory.get_hosts(), key=lambda x: (x.vars['is_jail'], x.name)):
        groups = [group.name for group in host.get_groups()]
        groups.sort()
        _vars = combine_vars(host.get_group_vars(), host.vars)
        separator = '{} host -- {} --'.format("---" * 30, host.name)
        output['hosts'][host.name] = {'...': separator, 'groups': groups, 'vars': _vars}
    for group in sorted(inventory.groups.values(), key=lambda x: x.name):
        hosts = [host.name for host in group.get_hosts()]
        hosts.sort()
        _vars = group.get_vars()
        separator = '{} group -- {} --'.format("---" * 30, group.name)
        output['groups'][group.name] = {'...': separator, 'hosts': hosts, 'vars': _vars}
    return json.dumps(output, sort_keys=True, indent=4, separators=(',', ': '))


def main():
    if DEBUG:
        print('=' * 160)
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
    handle, list_path = tempfile.mkstemp(dir='./hosts/', text=True)
    update_hosts(inventory, list_path)
    update_features(inventory, list_path)
    os.remove(list_path)
    update_vars(inventory)
    update_variables(inventory)
    if DEBUG:
        print('=' * 80)
        output = debug_output(inventory)
    else:
        output = ansible_output(inventory)
    print(output)
    if DEBUG:
        print('=' * 160)


if __name__ == "__main__":
    main()
