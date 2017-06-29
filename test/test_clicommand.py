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

# pylint: disable=R0903

""" Unit tests for CLI """

import unittest
import sys
from rho.clicommands import AuthAddCommand, AuthListCommand, \
    AuthClearCommand, AuthEditCommand, ProfileAddCommand, \
    ProfileClearCommand, ProfileEditCommand, \
    ProfileListCommand, ScanCommand


class HushUpStderr(object):
    """Class used to quiet standard error output"""
    def write(self, stream):
        """Ignore standard error output"""
        pass


class CliCommandsTests(unittest.TestCase):
    """Class for testing the various cli commands for rho"""
    def setUp(self):
        # Temporarily disable stderr for these tests, CLI errors clutter up
        # nosetests command.
        self.orig_stderr = sys.stderr
        sys.stderr = HushUpStderr()

    def tearDown(self):
        # Restore stderr
        sys.stderr = self.orig_stderr

    def _run_test(self, cmd, args):  # pylint: disable=no-self-use
        sys.argv = ["bin/rho"] + args
        cmd.main()

    def test_scan_facts_default(self):
        """Test utilizing the scan command exercising the collection
        the default facts with 100 ansible forks
        """
        try:
            self._run_test(ScanCommand(), ["scan", "--profile", "profilename",
                                           "--reset", "--reportfile",
                                           "data/test_report.csv", "--facts",
                                           "default", "ansible_forks",
                                           "100"])
        except SystemExit:
            pass

    def test_scan_facts_file(self):
        """Test utilizing the scan command exercising the collection
        the facts from an input facts file with 100 ansible forks
        """
        try:
            self._run_test(ScanCommand(), ["scan", "--profile", "profilename",
                                           "--reset", "--reportfile",
                                           "data/test_report.csv", "--facts",
                                           "data/facts_test", "ansible_forks",
                                           "100"])
        except SystemExit:
            pass

    def test_scan_facts_list(self):
        """Test utilizing the scan command exercising the collection
        the facts from an input facts list with 100 ansible forks
        """
        try:
            self._run_test(ScanCommand(),
                           ["scan", "--profile", "profilename",
                            "--reset", "--reportfile",
                            "data/test_report.csv", "--facts",
                            "Username_uname.all",
                            "RedhatRelease_redhat-release.release",
                            "--ansible_forks",
                            "100"])
        except SystemExit:
            pass

    def test_profile_list(self):
        """Testing the profle list command execution"""
        self._run_test(ProfileListCommand(), ["profile", "list"])

    def test_profile_add_hosts_list(self):
        """Test the profile command adding a profile with a list and
        range of hosts and an ordered list of auths
        """
        try:
            self._run_test(ProfileAddCommand(), ["profile", "add", "--name",
                                                 "profilename", "hosts",
                                                 "1.2.3.4", "1.2.3.[4:100]",
                                                 "--auths", "auth_1", "auth2"])
        except SystemExit:
            pass

    def test_profile_add_hosts_file(self):
        """Test the profile command adding a profile with a file of hosts
        and an ordered list of auths
        """
        try:
            self._run_test(ProfileAddCommand(), ["profile", "add", "--name",
                                                 "profilename", "hosts",
                                                 "data/hosts_test", "--auths",
                                                 "auth_1", "auth2"])
        except SystemExit:
            pass

    def test_auth_list(self):
        """Testing the auth list command execution"""
        self._run_test(AuthListCommand(), ["auth", "list"])

    def test_profile_add_nonexist_auth(self):
        """Test the proile add command with an non-existent auth
        in order to catch error case
        """
        self.assertRaises(SystemExit, self._run_test, ProfileAddCommand(),
                          ["profile", "add", "--name", "profile", "hosts",
                           "1.2.3.4", "--auth", "doesnotexist"])

    def test_bad_range_options(self):
        """Test profile add command with an invalid host range"""
        # Should fail scanning range without a username:
        self.assertRaises(SystemExit, self._run_test, ProfileAddCommand(),
                          ["profile", "add", "--name",
                           "profilename", "hosts",
                           "a:d:b:s", "--auths",
                           "auth_1", "auth2"])

    def test_a_auth_add(self):
        """Testing the auth add command execution"""
        self._run_test(AuthAddCommand(), ["auth", "add", "--name", "auth1",
                                          "--username", "user", "--sshkeyfile",
                                          "./privatekey"])

    def test_a_profile_add(self):
        """Testing the profile add command execution"""
        self._run_test(ProfileAddCommand(), ["profile", "add", "--name", "p1",
                                             "--hosts", "1.2.3.4",
                                             "--auth", "auth1"])

    def test_auth_edit(self):
        """Testing the auth edit command execution"""
        self._run_test(AuthEditCommand(), ["auth", "edit", "--name", "auth1",
                                           "--username", "user",
                                           "--sshkeyfile", "./privatekey"])

    def test_profile_edit(self):
        """Testing the profile edit command execution"""
        self._run_test(ProfileEditCommand(), ["profile", "edit", "--name",
                                              "p1", "--hosts", "1.2.3.4",
                                              "--auth", "auth1"])

    def test_z_auth_clear_all(self):
        """Testing the auth clear all command execution"""
        self._run_test(AuthClearCommand(), ["auth", "clear", "--all"])

    def test_z_profile_clear_all(self):
        """Testing the profile clear all command execution"""
        self._run_test(ProfileClearCommand(), ["profile", "clear", "--all"])
