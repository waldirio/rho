#
# Copyright (c) 2009 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

# pylint: disable=too-few-public-methods

""" Unit tests for CLI """

import contextlib
import logging
import unittest
import sys
import os
import tempfile
import mock
import six
from rho import vault
from rho import utilities
from rho.authaddcommand import AuthAddCommand
from rho.authlistcommand import AuthListCommand
from rho.authclearcommand import AuthClearCommand
from rho.autheditcommand import AuthEditCommand
from rho.authshowcommand import AuthShowCommand
from rho.clicommand import CliCommand
from rho.factlistcommand import FactListCommand
from rho.profileaddcommand import ProfileAddCommand
from rho.profileclearcommand import ProfileClearCommand
from rho.profileeditcommand import ProfileEditCommand
from rho.profilelistcommand import ProfileListCommand
from rho.profileshowcommand import ProfileShowCommand
from rho.scancommand import ScanCommand

TEST_VAULT_PASSWORD = 'password'

TMP_VAULT_PASS = "/tmp/vault_pass"
TMP_FACTS = "/tmp/facts.txt"
TMP_HOSTS = "/tmp/hosts.txt"
TMP_TEST_REPORT = "/tmp/test_report.csv"


class HushUpStderr(object):
    """Class used to quiet standard error output"""
    def write(self, stream):
        """Ignore standard error output"""
        pass


@contextlib.contextmanager
def vault_json_list(value):
    """Run code with a new Vault-protected JSON list.

    After the code is finished, read back the value of the file and
    store it in `value`.

    :param value: the starting value of the Vault-protected JSON
    list. The final value will be written to this.
    """

    with tempfile.NamedTemporaryFile(delete=False) as temp_list:
        # Write the value to the temporary file
        this_vault = vault.Vault(TEST_VAULT_PASSWORD)
        this_vault.dump_as_json(value, stream=temp_list)
        temp_list.flush()

        # Run the code, making the file path available
        try:
            yield temp_list.name
        finally:
            # Read the (potentially modified) list file
            if os.path.isfile(temp_list.name):
                value[:] = this_vault.load_as_json(temp_list.name)
                os.unlink(temp_list.name)
            else:
                # The code might have deleted the file
                value[:] = []


@contextlib.contextmanager
def redirect_credentials(credentials):

    """Run code with a temporary credentials file.

    After the code is run, saves the new contents of the credentials
    file back into the list given.

    :param credentials: the credentials to run with, as a Python list.
    """

    with vault_json_list(credentials) as temp_creds:
        old_creds = utilities.CREDENTIALS_PATH
        try:
            utilities.CREDENTIALS_PATH = temp_creds
            yield
        finally:
            utilities.CREDENTIALS_PATH = old_creds


@contextlib.contextmanager
def redirect_profiles(profiles):
    """Run code with a temporary profiles file.

    After the code is run, saves the new contents of the profiles
    file back into the list given.

    :param profiles: the profiles to run with, as a Python list.
    """

    with vault_json_list(profiles) as temp_profiles:
        old_profiles = utilities.PROFILES_PATH
        try:
            utilities.PROFILES_PATH = temp_profiles
            yield
        finally:
            utilities.PROFILES_PATH = old_profiles


@contextlib.contextmanager
def redirect_stdout(stream):
    """Run a code block, capturing stdout to the given stream"""

    old_stdout = sys.stdout
    try:
        sys.stdout = stream
        yield
    finally:
        sys.stdout = old_stdout


# pylint: disable=too-many-public-methods, no-self-use
class CliCommandsTests(unittest.TestCase):
    """Class for testing the various cli commands for rho"""
    def setUp(self):
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()
        if os.path.isfile('data'):
            os.remove('data')

        if os.path.isfile(TMP_VAULT_PASS):
            os.remove(TMP_VAULT_PASS)
        with open(TMP_VAULT_PASS, 'w') as vault_pass_file:
            vault_pass_file.write(TEST_VAULT_PASSWORD)

        if os.path.isfile(TMP_FACTS):
            os.remove(TMP_FACTS)
        with open(TMP_FACTS, 'w') as facts_file:
            # Username_uname.hostname
            # Username_uname.os
            # Date_date.date
            # Cpu_cpu.bogomips
            # Cpu_cpu.vendor_id
            # RedhatRelease_redhat-release.name
            # RedhatPackages_redhat-packages.num_installed_packages
            facts_file.write('Username_uname.hostname\n')
            facts_file.write('Username_uname.os\n')
            facts_file.write('Date_date.date\n')
            facts_file.write('Cpu_cpu.bogomips\n')
            facts_file.write('Cpu_cpu.vendor_id\n')
            facts_file.write('RedhatRelease_redhat-release.name\n')

        if os.path.isfile(TMP_HOSTS):
            os.remove(TMP_HOSTS)
        with open(TMP_HOSTS, 'w') as hosts_file:
            # 192.168.124.[1:40]
            # 192.168.121.007
            # 192.168.121.140
            # 192.168.124.153
            # 192.168.124.[150:200]
            hosts_file.write('192.168.124.[1:40]\n')
            hosts_file.write('192.168.121.007\n')
            hosts_file.write('192.168.121.140\n')
            hosts_file.write('192.168.124.153\n')
            hosts_file.write('192.168.124.[150:200]\n')

    def tearDown(self):
        # Restore stderr
        sys.stderr = self.orig_stderr
        if os.path.isfile('data'):
            os.remove('data')

        if os.path.isfile(TMP_VAULT_PASS):
            os.remove(TMP_VAULT_PASS)

        if os.path.isfile(TMP_FACTS):
            os.remove(TMP_FACTS)

        if os.path.isfile(TMP_HOSTS):
            os.remove(TMP_HOSTS)

    # pylint: disable=unused-argument
    @mock.patch('uuid.uuid4', return_value=1)
    def test_auth_add(self, uuid4):
        """Testing the auth add command execution"""

        sys.argv = ['/bin/rho', "auth", "add", "--name", "auth_1",
                    "--username", "user", "--sshkeyfile",
                    "./privatekey", "--vault",
                    TMP_VAULT_PASS]

        creds = list()
        with redirect_credentials(creds):
            AuthAddCommand().main()
        self.assertEqual(creds,
                         [{u'id': u'1',
                           u'name': u'auth_1',
                           u'username': u'user',
                           u'password': None,
                           u'sudo_password': None,
                           u'ssh_key_file': u'./privatekey'}])

    # pylint: disable=unused-argument
    @mock.patch('uuid.uuid4', return_value=2)
    def test_auth_add_again(self, uuid4):
        """Testing the auth add command execution"""

        sys.argv = ['/bin/rho', "auth", "add", "--name", "auth_2",
                    "--username", "user", "--sshkeyfile",
                    "./privatekey", "--vault",
                    TMP_VAULT_PASS]

        creds = [{u'id': u'1', u'name': u'auth_1', u'username': u'user',
                  u'password': u'', u'sudo_password': None,
                  u'ssh_key_file': u'./privatekey'}]

        with redirect_credentials(creds):
            AuthAddCommand().main()

        self.assertEqual(creds,
                         [{u'id': u'1',
                           u'name': u'auth_1',
                           u'username': u'user',
                           u'password': u'',
                           u'sudo_password': None,
                           u'ssh_key_file': u'./privatekey'},
                          {u'id': u'2',
                           u'name': u'auth_2',
                           u'username': u'user',
                           u'password': None,
                           u'sudo_password': None,
                           u'ssh_key_file': u'./privatekey'}])

    def test_auth_list(self):
        """Testing the auth list command execution"""

        sys.argv = ['/bin/rho', "auth", "list", "--vault",
                    TMP_VAULT_PASS]
        auth_list_out = six.StringIO()
        with redirect_credentials([
            {'id': '1', 'name': 'name', 'username': 'username',
             'password': 'password', 'ssh_key_file': 'file'}]):
            with redirect_stdout(auth_list_out):
                AuthListCommand().main()

        self.assertEqual(auth_list_out.getvalue().replace('\n', '')
                         .replace(' ', '').strip(),
                         '[{"id":"1","name":"name",' +
                         '"password":"' + utilities.PASSWORD_MASKING +
                         '",' + '"ssh_key_file":"file",' +
                         '"username":"username"}]')

    def test_auth_edit(self):
        """Testing the auth edit command execution"""

        sys.argv = ['/bin/rho', "auth", "edit", "--name", "auth_1",
                    "--username", "user_2",
                    "--sshkeyfile", "file_2",
                    "--vault", TMP_VAULT_PASS]
        creds = [{'id': '1', 'name': 'auth_1', 'username': 'user_1',
                  'password': 'password', 'ssh_key_file': 'file_1'}]
        with redirect_credentials(creds):
            AuthEditCommand().main()

        self.assertEqual(creds,
                         [{'id': '1',
                           'name': 'auth_1',
                           'username': 'user_2',
                           'password': 'password',
                           'ssh_key_file': 'file_2'}])

    def test_auth_show(self):
        """Testing the auth show command execution"""

        sys.argv = ['/bin/rho', "auth", "show", "--name", "auth_1",
                    "--vault", TMP_VAULT_PASS]
        creds = [{'id': '1', 'name': 'auth_1', 'username': 'user_1',
                  'password': 'password', 'ssh_key_file': 'file_1'}]
        auth_show_out = six.StringIO()
        with redirect_credentials(creds):
            with redirect_stdout(auth_show_out):
                AuthShowCommand().main()

        self.assertEqual(auth_show_out.getvalue().replace('\n', '')
                         .replace(' ', '').strip(),
                         '{"id":"1","name":"auth_1","password":"' +
                         utilities.PASSWORD_MASKING + '",' +
                         '"ssh_key_file":"file_1","username":"user_1"}')

    def test_auth_clear_all(self):
        """Testing the auth clear all command execution"""

        sys.argv = ['/bin/rho', "auth", "clear", "--all",
                    "--vault", TMP_VAULT_PASS]
        creds = [{'id': '1', 'name': 'auth_1', 'username': 'user_1',
                  'password': 'password', 'ssh_key_file': 'file_1'},
                 {'id': '2', 'name': 'auth_2', 'username': 'user_2',
                  'password': 'password', 'ssh_key_file': 'file_2'}]
        with redirect_credentials(creds):
            AuthClearCommand().main()
        self.assertEqual(creds, [])

    def test_fact_list(self):
        """Test that the 'fact list' command finishes successfully"""

        sys.argv = ['/bin/rho', 'fact', 'list']
        FactListCommand().main()

    def test_profile_add_hosts_list(self):
        """Test the profile command adding a profile with a list and
        range of hosts and an ordered list of auths
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "profile", "add", "--name",
                        "profilename", "hosts",
                        "1.2.3.4", "1.2.3.[4:100]",
                        "--auths", "auth_1", "auth2",
                        "--vault", TMP_VAULT_PASS]
            with redirect_credentials([
                {'id': '1', 'name': 'auth_1',
                 'username': 'username', 'password': 'password',
                 'ssh_key_file': 'file'}]):
                ProfileAddCommand().main()

    def test_profile_add_hosts_file(self):
        """Test the profile command adding a profile with a file of hosts
        and an ordered list of auths
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "profile", "add", "--name",
                        "profilename", "hosts",
                        TMP_HOSTS, "--auths",
                        "auth_1", "auth2",
                        "--vault", TMP_VAULT_PASS]
            with redirect_credentials([]):
                ProfileAddCommand().main()

    def test_profile_add_nonexist_auth(self):
        """Test the proile add command with an non-existent auth
        in order to catch error case
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "profile", "add", "--name", "profile",
                        "hosts", "1.2.3.4", "--auth", "doesnotexist",
                        "--vault", TMP_VAULT_PASS]
            with redirect_credentials([]):
                ProfileAddCommand().main()

    def test_profile_bad_range_options(self):
        """Test profile add command with an invalid host range"""

        # Should fail scanning range without a username:
        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "profile", "add", "--name",
                        "profilename", "hosts",
                        "a:d:b:s", "--auths",
                        "auth_1", "auth2",
                        "--vault", TMP_VAULT_PASS]
            with redirect_credentials([]):
                ProfileAddCommand().main()

    def test_profile_add(self):
        """Testing the profile add command execution"""

        sys.argv = ['/bin/rho', "profile", "add", "--name", "p1",
                    "--hosts", "1.2.3.4",
                    "--auth", "auth_1",
                    "--vault", TMP_VAULT_PASS]
        profiles = []
        with redirect_credentials([
            {'id': '1', 'name': 'auth_1',
             'username': 'username', 'password': 'password',
             'ssh_key_file': 'file'}]):
            with redirect_profiles(profiles):
                ProfileAddCommand().main()

        self.assertEqual(profiles,
                         [{'name': 'p1',
                           'hosts': ['1.2.3.4'],
                           'ssh_port': '22',
                           'auth': [{
                               'id': '1',
                               'name': 'auth_1'}]}])

    def test_profile_add_existing(self):
        """Testing the profile add command execution"""

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "profile", "add", "--name",
                        "p1", "--hosts", "1.2.3.4",
                        "--auth", "auth1",
                        "--vault", TMP_VAULT_PASS]
            with redirect_profiles([{
                'name': 'p1',
                'hosts': ['1.2.3.4'],
                'ssh_port': '22',
                'auth': [{
                    'id': '1',
                    'name': 'auth_1'}]}]):
                ProfileAddCommand().main()

    def test_profile_add_bad_port(self):
        """Testing the profile add command execution"""

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "profile", "add", "--name",
                        "p1", "--hosts", "1.2.3.4",
                        "--auth", "auth1", "--sshport", "abcd",
                        "--vault", TMP_VAULT_PASS]
            with redirect_profiles([{
                'name': 'p1',
                'hosts': ['1.2.3.4'],
                'ssh_port': '22',
                'auth': [{
                    'id': '1',
                    'name': 'auth_1'}]}]):
                ProfileAddCommand().main()

    def test_profile_edit(self):
        """Testing the profile edit command execution"""

        sys.argv = ['/bin/rho', "profile", "edit", "--name",
                    "p1", "--hosts", "1.2.3.4",
                    "--auth", "auth_1",
                    "--vault", TMP_VAULT_PASS]
        with redirect_credentials([
            {'id': '1', 'name': 'auth_1',
             'username': 'username', 'password': 'password',
             'ssh_key_file': 'file'}]):
            with redirect_profiles([{
                'name': 'p1',
                'hosts': ['1.2.3.4'],
                'ssh_port': '22',
                'auth': [{
                    'id': '1',
                    'name': 'auth_1'}]}]):
                ProfileEditCommand().main()

    def test_profile_list(self):
        """Testing the profle list command execution"""

        sys.argv = ['/bin/rho', "profile", "list",
                    "--vault", TMP_VAULT_PASS]
        profiles_list_out = six.StringIO()
        with redirect_credentials([]):
            with redirect_profiles([{
                'name': 'p1',
                'hosts': ['1.2.3.4'],
                'ssh_port': '22',
                'auth': [{
                    'id': '1',
                    'name': 'auth_1'}]}]):
                with redirect_stdout(profiles_list_out):
                    ProfileListCommand().main()

        # pylint: disable=bad-continuation
        self.assertEqual(profiles_list_out.getvalue(),  # noqa
'''[
    {
        "auth": [
            {
                "id": "1",
                "name": "auth_1"
            }
        ],
        "hosts": [
            "1.2.3.4"
        ],
        "name": "p1",
        "ssh_port": "22"
    }
]
''')

    def test_profile_show(self):
        """Testing the profile show command execution"""

        sys.argv = ['/bin/rho', "profile", "show", "--name",
                    "p1", "--vault", TMP_VAULT_PASS]
        profile_show_out = six.StringIO()
        with redirect_profiles([{
            'name': 'p1',
            'hosts': ['1.2.3.4'],
            'ssh_port': '22',
            'auth': [{
                'id': '1',
                'name': 'auth_1'}]}]):
            with redirect_stdout(profile_show_out):
                ProfileShowCommand().main()

        # pylint: disable=bad-continuation
        self.assertEqual(profile_show_out.getvalue(),  # noqa
'''{
    "auth": [
        {
            "id": "1",
            "name": "auth_1"
        }
    ],
    "hosts": [
        "1.2.3.4"
    ],
    "name": "p1",
    "ssh_port": "22"
}
''')

    def test_profile_clear_all(self):
        """Testing the profile clear all command execution"""

        sys.argv = ['/bin/rho', "profile", "clear", "--all",
                    "--vault", TMP_VAULT_PASS]

        profiles = [
            {'name': 'p1',
             'hosts': ['1.2.3.4'],
             'ssh_port': '22',
             'auth': [{
                 'id': '1',
                 'name': 'auth_1'}]},
            {'name': 'p2',
             'hosts': ['1.2.3.5'],
             'ssh_port': '22',
             'auth': [{
                 'id': '1',
                 'name': 'auth_1'}]}]
        with redirect_profiles(profiles):
            ProfileClearCommand().main()

        self.assertEqual(profiles, [])

    def test_scan_facts_no_profile(self):
        """Test utilizing the scan command catch no profile error
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "scan", "--reportfile",
                        TMP_TEST_REPORT, "--facts",
                        "default", "ansible_forks",
                        "100", "--vault", TMP_VAULT_PASS]
            with redirect_credentials([]):
                ScanCommand().main()

    def test_scan_facts_no_cache(self):
        """Test utilizing the scan command catch no cache error
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "scan", "--profile", "profilename",
                        "--cache", "--reportfile",
                        TMP_TEST_REPORT, "ansible_forks",
                        "100", "--vault", TMP_VAULT_PASS]
            with redirect_credentials([]):
                ScanCommand().main()

    def test_scan_facts_no_reportfile(self):
        """Test utilizing the scan command catch no report file error
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "scan", "--profile", "profilename",
                        "--facts", "default", "ansible_forks",
                        "100", "--vault", TMP_VAULT_PASS]
            with redirect_credentials([]):
                ScanCommand().main()

    def test_scan_facts_non_int_forks(self):
        """Test utilizing the scan command catch bad input for forks error
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "scan", "--profile", "profilename",
                        "--reportfile", TMP_TEST_REPORT,
                        "--facts", "default", "ansible_forks",
                        "a", "--vault", TMP_VAULT_PASS]
            with redirect_credentials([]):
                ScanCommand().main()

    def test_scan_facts_neg_int_forks(self):
        """Test utilizing the scan command catch bad input for forks error
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "scan", "--profile", "profilename",
                        "--reportfile",
                        TMP_TEST_REPORT, "--facts",
                        "default", "ansible_forks",
                        "-4", "--vault", TMP_VAULT_PASS]
            with redirect_credentials([]):
                ScanCommand().main()

    def test_scan_facts_default(self):
        """Test utilizing the scan command exercising the collection
        the default facts with 100 ansible forks
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "scan", "--profile", "profilename",
                        "--reportfile",
                        TMP_TEST_REPORT, "--facts",
                        "default", "ansible_forks",
                        "100", "--vault", TMP_VAULT_PASS]
            with redirect_credentials([]):
                ScanCommand().main()

    def test_scan_facts_file(self):
        """Test utilizing the scan command exercising the collection
        the facts from an input facts file with 100 ansible forks
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "scan", "--profile", "profilename",
                        "--reportfile",
                        TMP_TEST_REPORT, "--facts",
                        TMP_FACTS, "ansible_forks",
                        "100", "--vault", TMP_VAULT_PASS]
            ScanCommand().main()

    def test_scan_facts_list(self):
        """Test utilizing the scan command exercising the collection
        the facts from an input facts list with 100 ansible forks
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "scan", "--profile", "profilename",
                        "--reportfile",
                        TMP_TEST_REPORT, "--facts",
                        "uname.all",
                        "cpu.bogomips",
                        "--ansible_forks",
                        "100", "--vault", TMP_VAULT_PASS]
            with redirect_credentials([]):
                ScanCommand().main()

    def test_scan_facts_invalid_list(self):
        """Test utilizing the scan command exercising the collection
        the facts from an invalid facts list with 100 ansible forks
        """

        with self.assertRaises(SystemExit):
            sys.argv = ['/bin/rho', "scan", "--profile", "profilename",
                        "--reportfile",
                        TMP_TEST_REPORT, "--facts",
                        "bad.fact1", "bad.fact2", "ansible_forks",
                        "100", "--vault", TMP_VAULT_PASS]
            ScanCommand().main()

    def test_verbosity(self):
        """Test that -vv sets verbosity and log level correctly."""

        command = CliCommand()
        sys.argv = ['/bin/rho', '-vv']

        # CliCommand.main() will set up the command's environment but
        # not actually do anything.
        command.main()

        self.assertEqual(command.verbosity, 2)
        self.assertEqual(logging.getLogger().getEffectiveLevel(),
                         logging.DEBUG)
