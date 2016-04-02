#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import os
import sys

from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor

DEFAULT_PLAYBOOK_PATH = './playbooks/site.yml'
DEFAULT_HOST_LIST = './hosts/first_class_hosts'
DEFAULT_OPTIONS_LIST = ['listtags','listtasks', 'listhosts', 'syntax', 'connection',
    'module_path', 'forks', 'remote_user', 'private_key_file', 'ssh_common_args',
    'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method',
    'become_user', 'verbosity', 'check']
DEFAULT_OPTION_VALUES = {'listtags': False, 'listtasks': False, 'listhosts': False,
    'syntax': False, 'connection': 'ssh', 'module_path': None, 'forks': 100,
    'remote_user': 'root', 'private_key_file': None, 'ssh_common_args': None,
    'ssh_extra_args': None, 'sftp_extra_args': None, 'scp_extra_args': None,
    'become': True, 'become_method': None, 'become_user': 'root', 'verbosity': None,
    'check': False}
DEFAULT_EXTRA_VARS = {'tag': 'set_properties'}
DEFAULT_PASSWORDS = {}


def executor(playbook_path=DEFAULT_PLAYBOOK_PATH, host_list=DEFAULT_HOST_LIST,
               options_list=DEFAULT_OPTIONS_LIST, option_values=DEFAULT_OPTION_VALUES,
               extra_vars=DEFAULT_EXTRA_VARS, passwords=DEFAULT_PASSWORDS):
    """Returns a parametrizable playbook executor ready to be run inside a python script.
    Example:
    >>> from executors import executor
    >>> pbex = executor()
    >>> results = pbex.run()
    >>> print(results)
    """

    loader = DataLoader()
    variable_manager = VariableManager()
    inventory = Inventory(loader=loader,
                          variable_manager=variable_manager,
                          host_list=host_list)

    if not os.path.exists(playbook_path):
        print '[INFO] The playbook does not exist'
        sys.exit()

    Options = collections.namedtuple('Options', options_list)
    options = Options(**option_values)
    variable_manager.extra_vars = extra_vars
    return PlaybookExecutor(playbooks=[playbook_path],
                            inventory=inventory,
                            variable_manager=variable_manager,
                            loader=loader,
                            options=options,
                            passwords=passwords)
