# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Get the system's uname."""

import gettext

from ansible.module_utils import rho_cmd  # pylint: disable=no-name-in-module

T = gettext.translation('rho', 'locale', fallback=True)
_ = T.ugettext


# pylint: disable=too-few-public-methods
class UnameRhoCmd(rho_cmd.RhoCmd):
    """UnameRhoCmd is the wrapper for all cli commands
    to do with 'uname -<parameter>'. There are six
    fields currently associated with this class.
    There are 6 command strings in total that map
    one on one to each of the 6 fields.
    """

    def __init__(self):
        super(UnameRhoCmd, self).__init__()

        self.name = "uname"

        self.cmd_strings["uname.os"] = "uname -s"
        self.cmd_strings["uname.hostname"] = "uname -n"
        self.cmd_strings["uname.processor"] = "uname -p"
        self.cmd_strings["uname.kernel"] = "uname -r"
        self.cmd_strings["uname.all"] = "uname -a"
        self.cmd_strings["uname.hardware_platform"] = "uname -i"

        self.cmd_names["uname.os"] = ["uname.os"]
        self.cmd_names["uname.hostname"] = ["uname.hostname"]
        self.cmd_names["uname.processor"] = ["uname.processor"]
        self.cmd_names["uname.kernel"] = ["uname.kernel"]
        self.cmd_names["uname.all"] = ["uname.all"]
        self.cmd_names["uname.hardware_platform"] = ["uname.hardware_platform"]

        self.fields = {'uname.os': _('uname -s (os)'),
                       'uname.hostname': _('uname -n (hostname)'),
                       'uname.processor': _('uname -p (processor)'),
                       'uname.kernel': _('uname -r (kernel)'),
                       'uname.all': _('uname -a (all)'),
                       'uname.hardware_platform': _('uname -i '
                                                    '(hardware_platform)')}

    def parse_data(self):
        """This method loops through all requested cmd_strings'
        results and stores maps them to the respective
        fields in the report.
        """
        for cmd_name in self.cmd_names:
            if cmd_name in self.cmd_results.keys():
                if not (cmd_name == 'uname.kernel' and
                        self.cmd_results[cmd_name][1]):
                    self.data[self.cmd_names[cmd_name][0]] = \
                        self.cmd_results[cmd_name][0].strip()
