# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Get the system date, in a few different ways."""

import gettext

from ansible.module_utils import rho_cmd  # pylint: disable=no-name-in-module

T = gettext.translation('rho', 'locale', fallback=True)
_ = T.ugettext


# pylint: disable=too-few-public-methods
class DateRhoCmd(rho_cmd.RhoCmd):
    """DateRhoCmd has primarily one cmd_string i.e.'data'
    which is run to grab the system date.
    """

    def __init__(self):
        super(DateRhoCmd, self).__init__()
        self.name = "date"
        self.cmd_names['date'] = ['date.date']
        self.cmd_strings.update({
            'date': 'date',
            'anaconda_log':
            "ls --full-time /root/anaconda-ks.cfg "
            r"| grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}'",
            'machine_id':
            "ls --full-time /etc/machine-id "
            r"| grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}'",
            'filesystem_create':
            "fs_date=$(tune2fs -l $(mount "
            "                       | egrep '/ type' "
            "                       | grep -o '/dev.* on' "
            r"                      | sed -e 's/\on//g') "
            "          | grep 'Filesystem created' "
            r"         | sed 's/Filesystem created:\s*//g'); "
            "if [[ $fs_date ]]; "
            "then date +'%F' -d \"$fs_date\"; "
            "else echo "" ; "
            "fi",
            'yum_history':
            "yum history "
            "| tail -n 4 "
            r"| grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}'"})

        self.fields = {'date.date': _('date'),
                       'date.anaconda_log':
                       _("/root/anaconda-ks.cfg modified time"),
                       'date.machine_id':
                       _("/etc/machine-id modified time'"),
                       'date.filesystem_create':
                       _("uses tune2fs -l on the / filesystem dev "
                         "found using mount"),
                       'date.yum_history':
                       _("dates from yum history")}

    def parse_data(self):
        """This method parses the result of the cli command
        'date' and stores it in the only field date.date.
        """
        if hasattr(self.cmd_results, 'date'):
            self.data['date.date'] = self.cmd_results['date'][0].strip()
        if hasattr(self.cmd_results, 'anaconda_log'):
            self.data['date.anaconda_log'] = (
                self.cmd_results['anaconda_log'][0].strip())
        if hasattr(self.cmd_results, 'machine_id'):
            self.data['date.machine_id'] = (
                self.cmd_results['machine_id'][0].strip())
        if hasattr(self.cmd_results, 'filesystem_create'):
            self.data['date.filesystem_create'] = (
                self.cmd_results['filesystem_create'][0].strip())
        if hasattr(self.cmd_results, 'yum_history'):
            self.data['date.yum_history'] = (
                self.cmd_results['yum_history'][0].strip())
