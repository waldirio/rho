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
import os
import sys
import re
import time
import json
from collections import defaultdict
from getpass import getpass
import pexpect
import yaml
from rho import utilities
from rho.clicommand import CliCommand
from rho.vault import get_vault_and_password
from rho.utilities import (
    multi_arg, _read_in_file, str_to_ascii, iteritems, PING_LOG_PATH,
    ANSIBLE_LOG_PATH, SCAN_LOG_PATH, PING_INVENTORY_PATH, PROFILE_HOSTS_SUFIX,
    PROFILE_HOST_AUTH_MAPPING_SUFFIX, log
)
from rho.translation import _


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
    sudo_password = auth.get('sudo_password')

    ansible_vars = {}

    ansible_vars['ansible_user'] = str_to_ascii(username)
    if password:
        ansible_vars['ansible_ssh_pass'] = str_to_ascii(password)
    if ssh_key_file:
        ansible_vars['ansible_ssh_private_key_file'] = \
            str_to_ascii(ssh_key_file)
    if sudo_password:
        ansible_vars['ansible_become_pass'] = sudo_password

    return ansible_vars


def redacted_auth_string(auth):
    """Format an auth for the host auth mapping file.

    :param auth: the auth. A dictionary with fields 'id', 'name',
        'username', 'password', and 'ssh_key_file'.

    :returns: a string of the form
      'name, username, ********, ssh_key_file'
    """

    name = auth.get('name')
    username = auth.get('username')
    ssh_key_file = auth.get('ssh_key_file')

    return '{0}, {1}, {2}, {3}'.format(
        name, username, utilities.PASSWORD_MASKING, ssh_key_file)


def redact_dict(redact_key_list, a_dict):
    """Redact_values in a dictionary

    :param redact_key_list: keys in dictionary that value should be redacted
    :param a_dict: A dictionary to redact
    :returns: the redacted dictionary
    """
    for key in redact_key_list:
        if a_dict is not None and key in a_dict:
            a_dict[key] = utilities.PASSWORD_MASKING
    return a_dict


def log_yaml_inventory(label, inventory):
    """Log yaml inventory but mask passwords

    :param inventory: A dictionary of the ansible inventory
    """
    alpha = inventory.get('alpha')
    hosts_dict = alpha.get('hosts')
    vars_dict = alpha.get('vars')
    redact_key_list = ['ansible_become_pass', 'ansible_ssh_pass']

    # pylint: disable=unused-variable
    for host, host_dict in iteritems(hosts_dict):
        host_dict = redact_dict(redact_key_list, host_dict)

    vars_dict = redact_dict(redact_key_list, vars_dict)

    log.debug('%s:\n%s', label, yaml.dump(inventory))
    return inventory


def process_ping_output(out_lines):
    """Find successful hosts from the output of a ping command.

    Use this function by using ansible to run echo "Hello" on remote
    hosts, then sending the output to this function.

    :param out_lines: an iterator returning lines of Ansible output.
    :returns: the hosts that pinged successfully, as a set and those that
        failed, as a set.
    """

    success_hosts = set()
    failed_hosts = set()

    # Ansible output has the format
    # host | UNREACHABLE! => {
    #     "changed": false,
    #     "msg": "Failed to connect to the host via ssh ...",
    #     "unreachable": true
    #    }
    #   hostname | SUCCESS | rc=0 >>
    #   Hello
    # with the above two lines repeated for each host
    for line in out_lines:
        ansi_escape = re.compile(r'\x1b[^m]*m')
        line = ansi_escape.sub('', line)
        pieces = line.split('|')
        if len(pieces) == 3 and pieces[1].strip() == 'SUCCESS':
            success_hosts.add(pieces[0].strip())
        elif len(pieces) == 3 and pieces[1].strip() == 'FAILED':
            failed_hosts.add(pieces[0].strip())
        elif len(pieces) == 2 and pieces[1].strip().startswith('UNREACHABLE'):
            failed_hosts.add(pieces[0].strip())

    log.debug('Ping log reached hosts: %s', success_hosts)
    log.debug('Ping log did not reached hosts: %s', failed_hosts)

    return success_hosts, failed_hosts


# Creates the inventory for pinging all hosts and records
# successful auths and the hosts they worked on
# pylint: disable=too-many-statements, too-many-arguments, unused-argument
def _create_ping_inventory(vault, vault_pass, profile_ranges, profile_port,
                           credential, forks, ansible_verbosity):

    """Find which auths work with which hosts.

    :param vault: a Vault object
    :param vault_pass: password for the Vault?
    :param profile_ranges: hosts for the profile
    :param profile_port: the SSH port to use
    :param credential: auth to use
    :param forks: the number of Ansible forks to use

    :returns: a tuple of
      (list of IP addresses that worked for any auth,
       map from host IPs to SSH ports that worked with them,
       map from host IPs to lists of auths that worked with them
      )
    """

    # pylint: disable=too-many-locals
    success_hosts = set()
    failed_hosts = set()
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

    vars_dict = auth_as_ansible_host_vars(credential)

    yml_dict = {'alpha': {'hosts': hosts_dict, 'vars': vars_dict}}
    vault.dump_as_yaml_to_file(yml_dict, PING_INVENTORY_PATH)
    log_yaml_inventory('Ping inventory', yml_dict)

    cmd_string = 'ansible alpha -m raw' \
                 ' -i ' + PING_INVENTORY_PATH \
                 + ' --ask-vault-pass -f ' + forks \
                 + ' -a \'echo "Hello"\''

    my_env = os.environ.copy()
    my_env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    # Don't pass ansible_verbosity here as adding too much
    # verbosity can break our parsing of Ansible's output. This is
    # a temporary fix - a better solution would be less-fragile
    # output parsing.
    run_ansible_with_vault(cmd_string, vault_pass,
                           log_path=PING_LOG_PATH,
                           env=my_env,
                           log_to_stdout=True,
                           ansible_verbosity=0)

    with open(PING_LOG_PATH, 'r') as ping_log:
        success_hosts, failed_hosts = process_ping_output(ping_log)

    for host in success_hosts:
        success_auth_map[host].append(credential)
        success_port_map[host] = profile_port

    return list(success_hosts), success_port_map, success_auth_map, \
        list(failed_hosts)


# Helper function to create a file to store the mapping
# between hosts and ALL the auths that were ever succesful
# with them arranged according to profile and date of scan.
def _create_hosts_auths_file(success_auth_map, profile):
    host_auth_mapping = profile + PROFILE_HOST_AUTH_MAPPING_SUFFIX
    host_auth_mapping_path = utilities.get_config_path(host_auth_mapping)
    with open(host_auth_mapping_path, 'a') as host_auth_file:
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
                string_to_write += redacted_auth_string(auth)
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

    :returns: a dict with the structure:

        .. code-block:: python

            {'alpha':
                {'hosts':
                    {'IP address 1': {'host-vars-1'},
                     'IP address 2': {'host-vars-2'},
                     # ...
                    }
                }
            }
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
    hosts_yml = profile + PROFILE_HOSTS_SUFIX
    hosts_yml_path = utilities.get_config_path(hosts_yml)
    vault.dump_as_yaml_to_file(yml_dict, hosts_yml_path)
    log_yaml_inventory('Main inventory', yml_dict)


def run_ansible_with_vault(cmd_string, vault_pass, env=None, log_path=None,
                           log_to_stdout=True, ansible_verbosity=0):
    """ Runs ansible command allowing for password to be provided after
    process triggered.

    Returns after the process completes.

    :param cmd_string: the command to run.
    :param vault_pass: the password to the user's Ansible Vault.
    :param env: the environment to run the subprocess in.
    :param log_path: a path to write the process's log to. Defaults to
        'XDG_DATA_HOME/rho/ansible_log'.
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
        log_path = ANSIBLE_LOG_PATH

    if ansible_verbosity:
        cmd_string = cmd_string + ' -' + 'v' * ansible_verbosity

    result = None
    try:
        utilities.ensure_data_dir_exists()
        with open(log_path, 'wb') as logfile:
            pass
        with open(log_path, 'r+b') as logfile:
            log.debug('Running Ansible: %s', cmd_string)
            child = pexpect.spawn(cmd_string, timeout=None,
                                  env=env)

            if log_to_stdout:
                utilities.threaded_tailing(log_path, ansible_verbosity)

            result = child.expect('Vault password:')
            child.sendline(vault_pass)
            # Set the log file *after* we send the user's Vault
            # password to Ansible, so we don't log the password.
            child.logfile = logfile
            last_pos = logfile.tell()

            i = child.expect([pexpect.EOF, 'Enter passphrase for key .*:',
                              'you want to continue connecting (yes/no)?'])
            while i:
                new_pos = logfile.tell()
                logfile.seek(last_pos)
                logfile_lines = logfile.readlines()
                log.info(logfile_lines)
                print(logfile_lines[-1].replace('\r\n', ''))
                logfile.seek(new_pos)
                last_pos = new_pos
                child.logfile = None
                # Ansible has already printed a prompt; it would be
                # confusing if getpass printed another one.
                child.sendline(getpass(''))
                child.logfile = logfile
                i = child.expect([pexpect.EOF, 'Enter passphrase for key .*:',
                                  'you want to continue connecting (yes/no)?'])

            if child.isalive():
                child.wait()
            if log_to_stdout:
                time.sleep(2)

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

        self.parser.add_option("--cache", dest="cache", action="store_true",
                               metavar="RESET", default=False,
                               help=_("Use if profiles/auths previously "
                                      "discovered should be reused"))

        self.parser.add_option("--profile", dest="profile", metavar="PROFILE",
                               help=_("NAME of the profile - REQUIRED"))

        self.parser.add_option("--reportfile", dest="report_path",
                               metavar="REPORTFILE",
                               help=_("Report file path - REQUIRED"))

        self.parser.add_option("--facts", dest="facts", metavar="FACTS",
                               action="callback", callback=multi_arg,
                               default=[], help=_("'default', list or file"))

        self.parser.add_option("--scan-dirs", dest="scan_dirs",
                               metavar="SCANDIRS", action="callback",
                               callback=multi_arg, default=[],
                               help=_("list of remote directories to scan"))

        self.parser.add_option("--ansible-forks", dest="ansible_forks",
                               metavar="FORKS",
                               help=_("number of ansible forks"))

        self.parser.add_option("--vault", dest="vaultfile", metavar="VAULT",
                               help=_("file containing vault password for"
                                      " scripting"))

        self.parser.add_option("--logfile", dest="logfile", metavar="LOGFILE",
                               help=_("file to log scan output to"))

        self.facts_to_collect = None

    # pylint: disable=too-many-branches
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
                    print(_("--ansible-forks can only be a positive integer."))
                    self.parser.print_help()
                    sys.exit(1)
            except ValueError:
                print(_("--ansible-forks can only be a positive integer."))
                self.parser.print_help()
                sys.exit(1)

        # perform fact validation
        facts = self.options.facts
        if facts == [] or facts == ['default']:
            self.facts_to_collect = list(utilities.DEFAULT_FACTS)
        elif facts == ['all']:
            self.facts_to_collect = list(utilities.ALL_FACTS)
        elif facts == ['jboss']:
            self.facts_to_collect = list(utilities.JBOSS_FACTS_TUPLE +
                                         utilities.CONNECTION_FACTS_TUPLE)
        elif facts == ['rhel']:
            self.facts_to_collect = list(utilities.RHEL_FACTS +
                                         utilities.CONNECTION_FACTS_TUPLE)
        elif os.path.isfile(facts[0]):
            self.facts_to_collect = _read_in_file(facts[0])
        else:
            assert isinstance(facts, list)
            self.facts_to_collect = facts
        # check facts_to_collect has valid facts
        all_facts = utilities.ALL_FACTS
        facts_to_collect_set = set(self.facts_to_collect)
        if not facts_to_collect_set.issubset(all_facts):
            invalid_facts = facts_to_collect_set.difference(all_facts)
            print(_("Invalid facts were supplied to scan command: " +
                    ",".join(invalid_facts)))
            self.parser.print_help()
            sys.exit(1)

        if self.options.scan_dirs == []:
            self.options.scan_dirs = ['/', '/opt', '/app', '/home', '/usr']
        elif os.path.isfile(self.options.scan_dirs[0]):
            self.options.scan_dirs = \
                _read_in_file(self.options.scan_dirs[0])
        else:
            assert isinstance(self.options.scan_dirs, list)
        # check that all values in scan_dirs are valid abs paths
        invalid_paths = utilities.check_path_validity(self.options.scan_dirs)
        if invalid_paths != []:
            print(_("Invalid paths were supplied to the --scan-dirs option: " +
                    ",".join(invalid_paths)))
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
        hosts_yml = profile + PROFILE_HOSTS_SUFIX
        hosts_yml_path = utilities.get_config_path(hosts_yml)

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

        # cache is used when the profile/auth mapping has been previously
        # used and does not need to be rerun.
        if not self.options.cache:
            success_hosts = []
            success_port_map = {}
            auth_map = {}
            remaining_hosts = profile_ranges
            for cred_item in profile_auth_list:
                success_hosts_, success_port_map_, \
                    auth_map_, remaining_hosts_ = \
                    _create_ping_inventory(vault, vault_pass,
                                           remaining_hosts,
                                           profile_port,
                                           cred_item, forks,
                                           self.verbosity)
                success_hosts = success_hosts + success_hosts_
                remaining_hosts = remaining_hosts_
                success_port_map.update(success_port_map_)
                auth_map.update(auth_map_)
            if not success_hosts:
                print(_('All auths are invalid for this profile'))
                sys.exit(1)

            _create_hosts_auths_file(auth_map, profile)

            _create_main_inventory(vault, success_hosts, success_port_map,
                                   auth_map, profile)

        elif os.path.isfile(hosts_yml_path):
            print("Profile '" + profile + "' has not been processed. " +
                  "Please run without using --cache with the profile first.")
            sys.exit(1)

        # always output connection.x
        for key in utilities.CONNECTION_FACTS_TUPLE:
            if key not in self.facts_to_collect:
                self.facts_to_collect.append(key)

        scan_dirs = ' '.join(self.options.scan_dirs)
        ansible_vars = {'facts_to_collect': self.facts_to_collect,
                        'report_path': report_path,
                        'scan_dirs': scan_dirs}

        playbook = utilities.PLAYBOOK_DEV_PATH
        if not os.path.isfile(playbook):
            playbook = utilities.PLAYBOOK_RPM_PATH
            if not os.path.isfile(playbook):
                print(_("rho scan playbook not found locally or in '%s'")
                      % playbook)
                sys.exit(1)

        cmd_string = ('ansible-playbook {playbook} '
                      '-i {inventory} -f {forks} '
                      '--ask-vault-pass '
                      '--extra-vars \'{vars}\'').format(
                          playbook=playbook,
                          inventory=hosts_yml_path,
                          forks=forks,
                          vars=json.dumps(ansible_vars))

        # process finally runs ansible on the
        # playbook and inventories thus created.
        if self.options.logfile:
            log_path = self.options.logfile
        else:
            log_path = SCAN_LOG_PATH
        print('Running:', cmd_string)
        process = run_ansible_with_vault(cmd_string, vault_pass,
                                         log_path=log_path,
                                         log_to_stdout=True,
                                         ansible_verbosity=self.verbosity)
        if process.exitstatus == 0 and process.signalstatus is None:
            host_auth_mapping = \
                self.options.profile + PROFILE_HOST_AUTH_MAPPING_SUFFIX
            host_auth_mapping_path = \
                utilities.get_config_path(host_auth_mapping)
            print(_("Scanning has completed. The mapping has been"
                    " stored in file '" + host_auth_mapping_path +
                    "'. The facts have been stored in '" +
                    report_path + "'"))
        else:
            print(_("An error has occurred during the scan. Please review" +
                    " the output to resolve the given issue."))
            sys.exit(1)
