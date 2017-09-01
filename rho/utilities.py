#
# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

""" A set of reusable methods common to many of the commands """

from __future__ import print_function
import os
import sys
import re
import csv
import tempfile
from shutil import move
import sh
from xdg.BaseDirectory import xdg_data_home, xdg_config_home
from rho.translation import _

if sys.version_info > (3,):
    import _thread
else:
    import thread as _thread  # pylint: disable=import-error

RHO_PATH = 'rho'
CONFIG_DIR = os.path.join(xdg_config_home, RHO_PATH)
DATA_DIR = os.path.join(xdg_data_home, RHO_PATH)
CREDENTIALS_PATH = os.path.join(CONFIG_DIR, 'credentials')
PROFILES_PATH = os.path.join(CONFIG_DIR, 'profiles')
PING_INVENTORY_PATH = os.path.join(CONFIG_DIR, 'ping-inventory.yml')
RHO_LOG = os.path.join(DATA_DIR, 'rho_log')
PING_LOG_PATH = os.path.join(DATA_DIR, 'ping_log')
ANSIBLE_LOG_PATH = os.path.join(DATA_DIR, 'ansible_log')
SCAN_LOG_PATH = os.path.join(DATA_DIR, 'scan_log')

PROFILE_HOSTS_SUFIX = '_hosts.yml'
PROFILE_HOST_AUTH_MAPPING_SUFFIX = '_host_auth_mapping'

PLAYBOOK_DEV_PATH = 'rho_playbook.yml'
PLAYBOOK_RPM_PATH = '/usr/share/ansible/rho/rho_playbook.yml'

PASSWORD_MASKING = '********'

SENSITIVE_FACTS_TUPLE = ('connection.host',
                         'connection.port',
                         'uname.all',
                         'uname.hostname')

CONNECTION_FACTS_TUPLE = ('connection.host',
                          'connection.port',
                          'connection.uuid')
UNAME_FACTS_TUPLE = ('uname.os',
                     'uname.hostname',
                     'uname.processor',
                     'uname.kernel',
                     'uname.all',
                     'uname.hardware_platform')

REDHAT_RELEASE_FACTS_TUPLE = ('redhat-release.name',
                              'redhat-release.version',
                              'redhat-release.release')

INSTNUM_FACTS_TUPLE = ('instnum.instnum',)

SYSID_FACTS_TUPLE = ('systemid.system_id',
                     'systemid.username')

CPU_FACTS_TUPLE = ('cpu.count',
                   'cpu.socket_count',
                   'cpu.vendor_id',
                   'cpu.bogomips',
                   'cpu.cpu_family',
                   'cpu.model_name',
                   'cpu.model_ver')

ETC_RELEASE_FACTS_TUPLE = ('etc_release.name',
                           'etc_release.version',
                           'etc_release.release')

ETC_ISSUE_FACTS_TUPLE = ('etc-issue.etc-issue',)

DMI_FACTS_TUPLE = ('dmi.bios-vendor',
                   'dmi.bios-version',
                   'dmi.system-manufacturer',
                   'dmi.processor-family')

VIRT_FACTS_TUPLE = ('virt.virt',
                    'virt.type',
                    'virt.num_guests',
                    'virt.num_running_guests')

RH_PKG_FACTS_TUPLE = ('redhat-packages.is_redhat',
                      'redhat-packages.num_rh_packages',
                      'redhat-packages.num_installed_packages',
                      'redhat-packages.last_installed',
                      'redhat-packages.last_built')

VIRT_WHAT_FACTS_TUPLE = ('virt-what.type',)

DATE_FACTS_TUPLE = ('date.date',
                    'date.anaconda_log',
                    'date.machine_id',
                    'date.filesystem_create',
                    'date.yum_history')

SUBMAN_FACTS_TUPLE = ('subman.cpu.core(s)_per_socket',
                      'subman.cpu.cpu(s)',
                      'subman.cpu.cpu_socket(s)',
                      'subman.virt.host_type',
                      'subman.virt.is_guest',
                      'subman.virt.uuid',
                      'subman.has_facts_file')

JBOSS_FACTS_TUPLE = ('jboss.installed-versions',
                     'jboss.deploy-dates',
                     'jboss.running-versions')

BRMS_FACTS_TUPLE = ('jboss.brms.kie-api-ver',
                    'jboss.brms.drools-core-ver',
                    'jboss.brms.kie-war-ver')

FUSE_FACTS_TUPLE = ('jboss.fuse.activemq-ver',
                    'jboss.fuse.camel-ver',
                    'jboss.fuse.cxf-ver')

RHEL_FACTS = SUBMAN_FACTS_TUPLE + DATE_FACTS_TUPLE \
    + VIRT_WHAT_FACTS_TUPLE + RH_PKG_FACTS_TUPLE + VIRT_FACTS_TUPLE \
    + DMI_FACTS_TUPLE + ETC_ISSUE_FACTS_TUPLE + ETC_RELEASE_FACTS_TUPLE \
    + CPU_FACTS_TUPLE + SYSID_FACTS_TUPLE + INSTNUM_FACTS_TUPLE \
    + REDHAT_RELEASE_FACTS_TUPLE + UNAME_FACTS_TUPLE

JBOSS_FACTS = JBOSS_FACTS_TUPLE + BRMS_FACTS_TUPLE + FUSE_FACTS_TUPLE

DEFAULT_FACTS = RHEL_FACTS + JBOSS_FACTS + CONNECTION_FACTS_TUPLE


def threaded_tailing(path, ansible_verbosity=0):
    """Follow and provide output using a thread
    :param path: path to file to follow
    :param ansible_verbosity: the verbosity level
    """

    _thread.start_new_thread(tail_and_follow, (path, ansible_verbosity))


def tail_and_follow(path, ansible_verbosity):
    """Follow and provide output
    :param path: tuple containing thepath to file to follow
    :param ansible_verbosity: the verbosity level
    """
    if len(path) > 0:  # pylint: disable=len-as-condition
        truncate = 1
        if ansible_verbosity:
            truncate = ansible_verbosity

        print_line = truncate
        plabook_started = False
        truncated = False

        # pylint: disable=no-member
        for line in sh.tail('-f', '-n', '+0', path, _iter=True):
            ansi_escape = re.compile(r'\x1b[^m]*m')
            logline = ansi_escape.sub('', line)
            line = line.strip('\n')
            if logline.startswith('Enter passphrase'):
                print(line)
            if line.startswith('TASK') or line.startswith('PLAY'):
                print(line)
                print_line = truncate
                plabook_started = True
                truncated = False
            elif print_line > 0:
                line_len = len(line)
                char_truncate = truncate * 100
                if line_len > char_truncate:
                    print(line[0:char_truncate] + '...')
                else:
                    print(line)
                print_line = print_line - 1
            elif print_line == 0 and not truncated and plabook_started:
                print(_('-- output truncated --'))
                truncated = True


def ensure_config_dir_exists():
    """Ensure the Rho configuration directory exists."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)


def ensure_data_dir_exists():
    """Ensure the Rho data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


# pylint: disable=unused-argument
def multi_arg(option, opt_str, value, parser):
    """Call back function for arg-parse
    for when arguments are multiple
    :param option: The option
    :param opt_str: The option string
    :param value: The value
    :param parser: The parser for handling the option
    """
    args = []
    for arg in parser.rargs:
        if arg[0] != "-":
            args.append(arg)
        else:
            del parser.rargs[:len(args)]
            break
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)


# Read in a file and make it a list
def _read_in_file(filename):
    result = None
    hosts = None
    try:
        hosts = open(os.path.expanduser(os.path.expandvars(filename)), "r")
        result = hosts.read().splitlines()
        hosts.close()
    except EnvironmentError as err:
        sys.stderr.write('Error reading from %s: %s\n' % (filename, err))
        hosts.close()
    return result


# Makes sure the hosts passed in are in a format Ansible
# understands.
def check_range_validity(range_list):
    """Checks the input range_list to see if it meets the Ansible
    range criteria
    :param range_list: list of hosts
    """
    # pylint: disable=anomalous-backslash-in-string
    regex_list = ['[0-9]*.[0-9]*.[0-9]*.\[[0-9]*:[0-9]*\]',
                  '[0-9]*.[0-9]*.\[[0-9]*:[0-9]*\].[0-9]*',
                  '[0-9]*.[0-9]*.\[[0-9]*:[0-9]*\].\[[0-9]*:[0-9]*\]',
                  '[a-zA-Z0-9-\.]+',
                  '[a-zA-Z0-9-\.]*\[[0-9]*:[0-9]*\]*[a-zA-Z0-9-\.]*',
                  '[a-zA-Z0-9-\.]*\[[a-zA-Z]*:[a-zA-Z]*\][a-zA-Z0-9-\.]*']

    for reg_item in range_list:
        match = False
        for reg in regex_list:
            matches = re.findall(reg, reg_item)
            if len(matches) == 1:
                match = True
        if not match:
            if len(reg_item) <= 1:
                print(_("No such hosts file."))

            print(_("Bad host name/range : '%s'") % reg_item)
            sys.exit(1)
    return True


def validate_port(arg):
    """Check that arg is a valid port.

    :param arg: either a string or an integer.
    :returns: The arg, as an integer.
    :raises: ValueError, if arg is not a valid port.
    """

    if isinstance(arg, str):
        try:
            arg = int(arg)
        except ValueError:
            raise ValueError('Port value %s'
                             ' should be a positive integer'
                             ' in the valid range (0-65535)' % arg)
    elif not isinstance(arg, int):
        raise ValueError('Port value %s should be a positive integer'
                         ' in the valid range (0-65535)' % arg)

    # We need to support both system and user ports (see
    # https://en.wikipedia.org/wiki/Registered_port) because we don't
    # know how the user will have configured their system.
    if arg < 0 or arg > 65535:
        raise ValueError('Port value %s should be a positive integer'
                         ' in the valid range (0-65535)' % arg)

    return arg


def str_to_ascii(in_string):
    """ Coverts unicode string to ascii string
    :param in_string: input string to convert to ascii
    :returns: ASCII encoded string
    """
    if sys.version_info.major == 2:
        return in_string.decode('utf-8').encode('ascii')

    return in_string


def iteritems(dictionary):
    """Iterate over a dictionary's (key, value) pairs using Python 2 or 3.

    :param dictionary: the dictionary to iterate over.
    """

    if sys.version_info.major == 2:
        return dictionary.iteritems()

    return dictionary.items()


def write_csv_data(keys, data, path):
    """ Write csv data with input fieldnames a dictionary of data and
    the file path to write to.
    :param keys: The field names and keys of the dictionary
    :param data: The dictionary of data to convert to csv
    :param path: The file path to write to
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as data_temp:
        # Construct the CSV writer
        writer = csv.DictWriter(
            data_temp, fieldnames=sorted(keys), delimiter=',')

        # Write a CSV header if necessary
        writer.writeheader()

        # Write the data
        for row in data:
            writer.writerow(row)
    data_temp.close()
    move(data_temp.name, path)


def get_config_path(filename):
    """ Provides the path for a configuration filename
    :param filename: The filename to return the config path for
    :returns path to for filename in XDG_CONFIG_HOME associated with rho
    """
    return os.path.join(xdg_config_home, RHO_PATH, filename)
