#
# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

# pylint: disable=too-few-public-methods, too-many-lines

""" Rho CLI Commands """

from __future__ import print_function
import logging
import yaml
import os
import sys
import re
import time
import json
import subprocess
from collections import defaultdict
import pexpect
from rho import utilities
from rho.clicommand import CliCommand
from rho.vault import get_vault_and_password
from rho.utilities import multi_arg, _read_in_file, str_to_ascii, iteritems
from rho.translation import _


# Read ssh key from file
def _read_key_file(filename):
    keyfile = open(os.path.expanduser(
        os.path.expandvars(filename)), "r")
    sshkey = keyfile.read()
    keyfile.close()
    return sshkey


def auth_as_ansible_host_vars(auth):
    """Get the Ansible host vars that implement an auth.

    :param auth: the auth. A dictionary with fields 'id', 'name',
        'username', 'password', and 'ssh_key_file'.

    :returns: a dict that can be used as the host variables in an
        Ansible inventory.
    """

    username = auth.get('username')
    password = auth.get('password')
    ssh_key_file = auth.get('ssh_key_file')

    ansible_vars = {}

    ansible_vars['ansible_user'] = str_to_ascii(username)
    if password:
        ansible_vars['ansible_ssh_pass'] = str_to_ascii(password)
    if ssh_key_file:
        ansible_vars['ansible_ssh_private_key_file'] = \
            str_to_ascii(ssh_key_file)

    return ansible_vars


def format_auth_for_host_auth_mapping(auth):
    """Format an auth for the host auth mapping file.

    :param auth: the auth. A dictionary with fields 'id', 'name',
        'username', 'password', and 'ssh_key_file'.

    :returns: a string of the form
      'name, username, ********, ssh_key_file'
    """

    name = auth.get('name')
    username = auth.get('username')
    ssh_key_file = auth.get('ssh_key_file')

    return '{0}, {1}, ********, {2}'.format(
        name, username, ssh_key_file)


# Creates the inventory for pinging all hosts and records
# successful auths and the hosts they worked on
# pylint: disable=too-many-statements, too-many-arguments, unused-argument
def _create_ping_inventory(vault, vault_pass, profile_ranges, profile_port,
                           profile_auth_list, forks, ansible_verbosity):
    """Find which auths work with which hosts.

    :param vault: a Vault object
    :param vault_pass: password for the Vault?
    :param profile_ranges: hosts for the profile
    :param profile_port: the SSH port to use
    :param profile_auth_list: auths to use
    :param forks: the number of Ansible forks to use

    :returns: a tuple of
      (list of IP addresses that worked for any auth,
       map from host IPs to a list of all auths that worked with
         that host,
       map from host IPs to SSH ports that worked with them,
       map from host IPs to lists of auths that worked with them
      )
    """

    # pylint: disable=too-many-locals
    success_hosts = set()
    success_port_map = defaultdict()
    success_auth_map = defaultdict(list)
    hosts_dict = {}

    for profile_range in profile_ranges:
        # pylint: disable=anomalous-backslash-in-string
        reg = "[0-9]*.[0-9]*.[0-9]*.\[[0-9]*:[0-9]*\]"
        profile_range = profile_range.strip(',').strip()
        hostname = str_to_ascii(profile_range)
        if not re.match(reg, profile_range):
            hosts_dict[profile_range] = {'ansible_host': profile_range,
                                         'ansible_port': profile_port}
        else:
            hosts_dict[hostname] = None

    for cred_item in profile_auth_list:
        cred_pass = cred_item.get('password')
        cred_sshkey = cred_item.get('ssh_key_file')

        vars_dict = auth_as_ansible_host_vars(cred_item)

        yml_dict = {'all': {'hosts': hosts_dict, 'vars': vars_dict}}
        logging.debug('Ping inventory:\n%s', yaml.dump(yml_dict))
        vault.dump_as_yaml_to_file(yml_dict, 'data/ping-inventory.yml')

        cmd_string = 'ansible all -m' \
                     ' ping  -i data/ping-inventory.yml --ask-vault-pass -f ' \
                     + forks

        my_env = os.environ.copy()
        my_env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
        # Don't pass ansible_verbosity here as adding too much
        # verbosity can break our parsing of Ansible's output. This is
        # a temporary fix - a better solution would be less-fragile
        # output parsing.
        run_ansible_with_vault(cmd_string, vault_pass,
                               log_path='data/ping_log',
                               env=my_env,
                               log_to_stdout=True,
                               ansible_verbosity=0)

        with open('data/ping_log', 'r') as ping_log:
            out = ping_log.readlines()

        # pylint: disable=unused-variable
        for linenum, line in enumerate(out):
            if 'pong' in out[linenum]:
                host_line = out[linenum - 2].replace('\x1b[0;32m', '')
                host_ip = host_line.split('|')[0].strip()
                success_hosts.add(host_ip)
                success_auth_map[host_ip].append(cred_item)
                success_port_map[host_ip] = profile_port

    return list(success_hosts), success_port_map, success_auth_map


# Helper function to create a file to store the mapping
# between hosts and ALL the auths that were ever succesful
# with them arranged according to profile and date of scan.
def _create_hosts_auths_file(success_auth_map, profile):
    with open('data/' + profile + '_host_auth_mapping', 'a') as host_auth_file:
        string_to_write = time.strftime("%c") + '\n-' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---' \
                                                '---\n'
        for host, line in iteritems(success_auth_map):
            string_to_write += host + '\n----------------------\n'
            for auth in line:
                string_to_write += format_auth_for_host_auth_mapping(auth)
            string_to_write += '\n\n'
        string_to_write += '\n*******************************' \
                           '*********************************' \
                           '**************\n\n'
        host_auth_file.write(string_to_write)


# Creates the filtered main inventory on which the custom
# modules to collect facts are run. This inventory can be
# used multiple times later after a profile has first been
# processed and the valid mapping as been figured out by
# pinging.
# pylint: disable=too-many-locals
def make_inventory_dict(success_hosts, success_port_map, auth_map):
    """Make the inventory for the scan, as a dict.

    :param success_hosts: a list of hosts for the inventory
    :param success_port_map: mapping from hosts to SSH ports
    :param auth_map: map from host IP to a list of auths it works with
    
    :returns: a dict with the structure
    {'alpha':
      {'hosts'
        {'IP address 1': {host-vars-1},
         'IP address 2': {host-vars-2},
         ...}}}
    """

    yml_dict = {}

    # Create section of successfully connected hosts
    alpha_hosts = {}
    for host in success_hosts:
        ascii_host = str_to_ascii(host)
        ascii_port = str_to_ascii(str(success_port_map[host]))
        host_vars = {'ansible_host': ascii_host,
                     'ansible_port': ascii_port}
        host_vars.update(auth_as_ansible_host_vars(auth_map[host][0]))
        alpha_hosts[ascii_host] = host_vars

    yml_dict['alpha'] = {'hosts': alpha_hosts}

    return yml_dict
    

def _create_main_inventory(vault, success_hosts, success_port_map,
                           auth_map, profile):
    yml_dict = make_inventory_dict(success_hosts, success_port_map, auth_map)

    logging.debug('Main inventory:\n%s', yaml.dump(yml_dict))
    vault.dump_as_yaml_to_file(yml_dict, 'data/' + profile + '_hosts.yml')


def run_ansible_with_vault(cmd_string, vault_pass, ssh_key_passphrase=None,
                           env=None, log_path=None, log_to_stdout=True,
                           ansible_verbosity=0):
    """ Runs ansible command allowing for password to be provided after
    process triggered.

    Returns after the process completes.

    :param cmd_string: the command to run.
    :param vault_pass: the password to the user's Ansible Vault.
    :param ssh_key_passphrase: the password for the user's SSH key(s).
    :param env: the environment to run the subprocess in.
    :param log_path: a path to write the process's log to. Defaults to
        'data/ansible_log'.
    :param log_to_stdout: if True, write Ansible's log to stdout. Defaults to
        True.
    :param ansible_verbosity: the number of v's of Ansible verbosity.
    :returns: the popen.spawn object for the process.
    """

    # pexpect provides the ability to send the process's output to a
    # single Python file object. We want to send it to a file and
    # maybe also stdout. The solution is to have pexpect log to the
    # file and then use 'tail -f' to copy that to stdout.

    if not log_path:
        log_path = 'data/ansible_log'

    if ansible_verbosity:
        cmd_string = cmd_string + ' -' + 'v' * ansible_verbosity

    result = None
    try:
        with open(log_path, 'wb') as logfile:
            child = pexpect.spawn(cmd_string, timeout=None,
                                  env=env)

            if log_to_stdout:
                tail = subprocess.Popen(['tail', '-f', '-n', '+0',
                                         '--pid={0}'.format(child.pid),
                                         log_path])

            result = child.expect('Vault password:')
            child.sendline(vault_pass)
            # Set the log file *after* we send the user's Vault
            # password to Ansible, so we don't log the password.
            child.logfile = logfile

            i = child.expect([pexpect.EOF, 'Enter passphrase for key .*:'])
            if i == 1:
                child.logfile = None
                child.sendline(ssh_key_passphrase)
                child.logfile = logfile
                child.expect(pexpect.EOF)

            if child.isalive():
                child.wait()
            if log_to_stdout:
                # tail will kill itself once it is done copying data
                # to stdout, thanks to the --pid option.
                tail.wait()

        return child
    except pexpect.EOF:
        print(str(result))
        print('pexpect unexpected EOF')
    except pexpect.TIMEOUT:
        print(str(result))
        print('pexpect timed out')


class ScanCommand(CliCommand):
    """ The command that performs the scanning and collection of
    facts by making the playbook, inventory and running ansible.
    """

    def __init__(self):
        usage = _("usage: %prog scan [options] PROFILE")
        shortdesc = _("scan given host profile")
        desc = _("scans the host profile")

        CliCommand.__init__(self, "scan", usage, shortdesc, desc)

        self.parser.add_option("--reset", dest="reset", action="store_true",
                               metavar="RESET", default=False,
                               help=_("Use if profiles/auths have been "
                                      "changed"))

        self.parser.add_option("--profile", dest="profile", metavar="PROFILE",
                               help=_("NAME of the profile - REQUIRED"))

        self.parser.add_option("--reportfile", dest="report_path",
                               metavar="REPORTFILE",
                               help=_("Report file path - REQUIRED"))

        self.parser.add_option("--facts", dest="facts", metavar="FACTS",
                               action="callback", callback=multi_arg,
                               default=[], help=_("'default', list or file"))

        self.parser.add_option("--ansible_forks", dest="ansible_forks",
                               metavar="FORKS",
                               help=_("number of ansible forks"))

        self.parser.add_option("--vault", dest="vaultfile", metavar="VAULT",
                               help=_("file containing vault password for"
                                      " scripting"))

        self.parser.add_option("--logfile", dest="logfile", metavar="LOGFILE",
                               help=_("file to log scan output to"))

        self.facts_to_collect = None

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.profile:
            print(_("No profile specified."))
            self.parser.print_help()
            sys.exit(1)

        if not self.options.report_path:
            print(_("No report location specified."))
            self.parser.print_help()
            sys.exit(1)

        if self.options.ansible_forks:
            try:
                if int(self.options.ansible_forks) <= 0:
                    print(_("ansible_forks can only be a positive integer."))
                    self.parser.print_help()
                    sys.exit(1)
            except ValueError:
                print(_("ansible_forks can only be a positive integer."))
                self.parser.print_help()
                sys.exit(1)

        # perform fact validation
        facts = self.options.facts
        if facts == [] or facts == ['default']:
            self.facts_to_collect = list(utilities.DEFAULT_FACTS_TUPLE)
        elif os.path.isfile(facts[0]):
            self.facts_to_collect = _read_in_file(facts[0])
        else:
            assert isinstance(facts, list)
            self.facts_to_collect = facts
        # check facts_to_collect is subset of utilities.DEFAULT_FACTS_TUPLE
        all_facts = utilities.DEFAULT_FACTS_TUPLE
        facts_to_collect_set = set(self.facts_to_collect)
        if not facts_to_collect_set.issubset(all_facts):
            invalid_facts = facts_to_collect_set.difference(all_facts)
            print(_("Invalid facts were supplied to scan command: " +
                    ",".join(invalid_facts)))
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        vault, vault_pass = get_vault_and_password(self.options.vaultfile)
        profile_found = False
        profile_auth_list = []
        profile_ranges = []
        profile_port = 22
        profile = self.options.profile
        forks = self.options.ansible_forks \
            if self.options.ansible_forks else '50'
        report_path = os.path.abspath(os.path.normpath(
            self.options.report_path))

        # Checks if profile exists and stores information
        # about that profile for later use.
        if not os.path.isfile(utilities.PROFILES_PATH):
            print(_('No profiles exist yet.'))
            sys.exit(1)

        if not os.path.isfile(utilities.CREDENTIALS_PATH):
            print(_('No auth credentials exist yet.'))
            sys.exit(1)

        profiles_list = vault.load_as_json(utilities.PROFILES_PATH)
        for curr_profile in profiles_list:
            if self.options.profile == curr_profile.get('name'):
                profile_found = True
                profile_ranges = curr_profile.get('hosts')
                profile_auths = curr_profile.get('auth')
                profile_port = curr_profile.get('ssh_port')
                cred_list = vault.load_as_json(utilities.CREDENTIALS_PATH)
                for auth in profile_auths:
                    for cred in cred_list:
                        if auth.get('id') == cred.get('id'):
                            profile_auth_list.append(cred)
                break

        if not profile_found:
            print(_("Invalid profile. Create profile first"))
            sys.exit(1)

        # reset is used when the profile has just been created
        # or freshly updated.
        if self.options.reset:
            success_hosts, success_port_map, auth_map = _create_ping_inventory(
                vault, vault_pass,
                profile_ranges,
                profile_port,
                profile_auth_list,
                forks,
                self.verbosity)

            if not success_hosts:
                print(_('All auths are invalid for this profile'))
                sys.exit(1)

            _create_hosts_auths_file(auth_map, profile)

            _create_main_inventory(vault, success_hosts, success_port_map,
                                   auth_map, profile)

        elif not os.path.isfile('data/' + profile + '_hosts'):
            print("Profile '" + profile + "' has not been processed. " +
                  "Please use --reset with profile first.")
            sys.exit(1)

        # always output connection.x
        for key in utilities.CONNECTION_FACTS_TUPLE:
            if key not in self.facts_to_collect:
                self.facts_to_collect.append(key)

        ansible_vars = {'facts_to_collect': self.facts_to_collect,
                        'report_path': report_path}

        playbook = utilities.PLAYBOOK_DEV_PATH
        if not os.path.isfile(playbook):
            playbook = utilities.PLAYBOOK_RPM_PATH
            if not os.path.isfile(playbook):
                print(_("rho scan playbook not found locally or in '%s'")
                      % playbook)
                sys.exit(1)

        cmd_string = ('ansible-playbook {playbook} '
                      '-i data/{profile}_hosts.yml -f {forks} '
                      '--ask-vault-pass '
                      '--extra-vars \'{vars}\'').format(
                          playbook=playbook,
                          profile=profile,
                          forks=forks,
                          vars=json.dumps(ansible_vars))

        # process finally runs ansible on the
        # playbook and inventories thus created.
        if self.options.logfile:
            log_path = self.options.logfile
        else:
            log_path = 'data/scan_log'
        print('Running:', cmd_string)
        process = run_ansible_with_vault(cmd_string, vault_pass,
                                         log_path=log_path,
                                         log_to_stdout=True,
                                         ansible_verbosity=self.verbosity)
        if process.exitstatus == 0 and process.signalstatus is None:
            print(_("Scanning has completed. The mapping has been"
                    " stored in file 'data/" + self.options.profile +
                    "_host_auth_mapping'. The facts have been stored in '" +
                    report_path + "'"))
        else:
            print(_("An error has occurred during the scan. Please review" +
                    " the output to resolve the given issue."))
