# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Unit tests for scancommand.py."""

# This file has tests for specific functions in rho.scancommand, but
# does not actually call ScanCommand.main(). The tests that do call
# main are in test_clicommand.py, becuase that's where the
# infrastructure for mocking out credentials and profiles is.

import unittest

from rho import inventory_scan


# pylint: disable=invalid-name
class TestInventoryDictFunctions(unittest.TestCase):
    """Unit tests for inventory_scan.py."""

    AUTH = {
        'id': '1',
        'name': 'auth_1',
        'username': 'user',
        'password': 'pass',
        'ssh_key_file': 'sshkey'}

    @staticmethod
    def auth_as_vars(hostname):
        """Generate Ansible auth vars for a hostname."""

        return {
            'ansible_host': hostname,
            'ansible_port': '22',
            'ansible_user': 'user',
            'ansible_ssh_pass': 'pass',
            'ansible_ssh_private_key_file': 'sshkey'}

    def test_make_inventory_dict_one_host(self):
        """Test inventory_scan.make_inventory_dict with just one host."""

        self.assertEqual(
            inventory_scan.make_inventory_dict(
                ['host_ip_1'],                # success_hosts
                {'host_ip_1': '22'},          # success_port_map
                {'host_ip_1': [self.AUTH]}),  # auth_map
            {'group0':
             {'hosts':
              {'host_ip_1': self.auth_as_vars('host_ip_1')}}})

    def test_round_trip(self):
        """Test make_inventory_dict with multiple groups."""

        val = inventory_scan.make_inventory_dict(
            ['host_ip_1', 'host_ip_2', 'host_ip_3'],
            {'host_ip_1': '22', 'host_ip_2': '22', 'host_ip_3': '22'},
            {'host_ip_1': [self.AUTH],
             'host_ip_2': [self.AUTH],
             'host_ip_3': [self.AUTH]},
            group_size=1)

        self.assertEqual(
            val,
            {'group0':
             {'hosts': {'host_ip_1': self.auth_as_vars('host_ip_1')}},
             'group1':
             {'hosts': {'host_ip_2': self.auth_as_vars('host_ip_2')}},
             'group2':
             {'hosts': {'host_ip_3': self.auth_as_vars('host_ip_3')}}})

        self.assertEqual(
            inventory_scan.hosts_by_group(val),
            {'group0': ['host_ip_1'],
             'group1': ['host_ip_2'],
             'group2': ['host_ip_3']})
