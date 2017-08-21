# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Tests for rho/authaddcommand.py."""

from collections import namedtuple
import unittest
import mock

from rho import authaddcommand


# pylint: disable=invalid-name, unused-argument, missing-docstring
class TestAuthAddCommand(unittest.TestCase):
    """Tests for rho/authaddcommand.py."""

    options = namedtuple('options',
                         ['name',
                          'username',
                          'password',
                          'filename',
                          'sudo_password'])

    @mock.patch('uuid.uuid4', return_value=1)
    @mock.patch('rho.authaddcommand.getpass', return_value='password')
    def test_make_auth_for_options_password(self, getpass, uuid4):
        options = self.options(
            name='auth_1',
            username='username',
            password=True,
            filename=None,
            sudo_password=False)

        self.assertEqual(
            authaddcommand.make_auth_for_options(options),
            {'id': '1',
             'name': 'auth_1',
             'username': 'username',
             'password': 'password',
             'ssh_key_file': None,
             'sudo_password': None})

    @mock.patch('uuid.uuid4', return_value=1)
    def test_make_auth_for_options_ssh_key(self, uuid4):
        options = self.options(
            name='auth_1',
            username='username',
            password=False,
            filename='ssh_key_file',
            sudo_password=False)

        self.assertEqual(
            authaddcommand.make_auth_for_options(options),
            {'id': '1',
             'name': 'auth_1',
             'username': 'username',
             'password': None,
             'ssh_key_file': 'ssh_key_file',
             'sudo_password': None})

    @mock.patch('uuid.uuid4', return_value=1)
    @mock.patch('rho.authaddcommand.getpass', return_value='sudopass')
    def test_make_auth_for_options_sudo_password(self, getpass, uuid4):
        options = self.options(
            name='auth_1',
            username='username',
            password=False,
            filename='ssh_key_file',
            sudo_password=True)

        self.assertEqual(
            authaddcommand.make_auth_for_options(options),
            {'id': '1',
             'name': 'auth_1',
             'username': 'username',
             'password': None,
             'ssh_key_file': 'ssh_key_file',
             'sudo_password': 'sudopass'})
