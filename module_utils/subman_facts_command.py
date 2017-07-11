# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Get information on subscription-manager."""

import gettext
from ansible.module_utils import rho_cmd  # pylint: disable=no-name-in-module

T = gettext.translation('rho', 'locale', fallback=True)
_ = T.ugettext


# pylint: disable=too-few-public-methods
class SubmanFactsRhoCmd(rho_cmd.RhoCmd):
    """This class wraps around the command strings
    that are meant to collect all information
    related to subscription-manager. It has
    6 fields associated to it currently. In total
    it contains 2 command strings one of which maps
    to the field subman.has_facts_file while the other
    maps to the rest: 'subman.cpu.core(s)_per_socket',
    'subman.cpu.cpu(s)', 'subman.cpu.cpu_socket(s)',
    'subman.virt.host_type', and  'subman.virt.is_guest'.
    """

    def __init__(self):
        super(SubmanFactsRhoCmd, self).__init__()

        self.name = "subscription-manager"

        self.cmd_strings["subman_facts_list"] \
            = 'subscription-manager facts --list'
        self.cmd_strings["subman_has_facts"] \
            = 'ls /etc/rhsm/facts | grep .facts'

        self.cmd_names['subman_facts_list'] \
            = ['subman.cpu.core(s)_per_socket',
               'subman.cpu.cpu(s)',
               'subman.cpu.cpu_socket(s)',
               'subman.virt.host_type',
               'subman.virt.is_guest']
        self.cmd_names['subman_has_facts'] = ['subman.hash_facts_file']

        self.fields = {'subman.cpu.core(s)_per_socket': _('cpu.core(s)_'
                                                          'per_socket '
                                                          '(from '
                                                          'subscription'
                                                          '-manager '
                                                          'facts --list)'),
                       'subman.cpu.cpu(s)': _('cpu.cpu(s)'
                                              '(from subscription'
                                              '-manager'
                                              ' facts --list)'),
                       'subman.cpu.cpu_socket(s)': _('cpu.cpu_socket(s)'
                                                     '(from'
                                                     'subscription-manager'
                                                     ' facts --list)'),
                       'subman.virt.host_type': _('virt.host_type'
                                                  '(from '
                                                  'subscription-manager'
                                                  ' facts --list)'),
                       'subman.virt.is_guest': _('virt.is_guest '
                                                 '(from '
                                                 'subscription-manager '
                                                 'facts --list)'),
                       'subman.has_facts_file': _('Whether '
                                                  'subscription-manager'
                                                  ' has a facts file')}

    def parse_data(self):
        """This method parses the output depending on which
        command string was requested to be run.
        """
        if 'subman_facts_list' in self.cmd_results.keys():
            if self.cmd_results['subman_facts_list'][0] \
                    and not self.cmd_results['subman_facts_list'][1]:
                result = self.cmd_results['subman_facts_list'][0].strip()
                result = [line.split(': ') for line in result.splitlines()]
                subman_facts = [("subman.%s" % field, value)
                                for field, value in result
                                if "subman.%s" % field
                                in self.fields.keys()]
                self.data.update(subman_facts)

        # Checks for the existence of at least
        # one .facts file in /etc/rhsm/facts
        if 'subman_has_facts' in self.cmd_results.keys():
            if self.cmd_results['subman_has_facts'][1]:
                self.data['subman.has_facts_file'] = 'error'
            elif self.cmd_results['subman_has_facts'][0]:
                fact_files_list = \
                    self.cmd_results['subman_has_facts'][0].strip().split('\n')
                # pylint: disable=len-as-condition
                self.data['subman.has_facts_file'] = "Y" \
                    if len(fact_files_list) > 0 else "N"
