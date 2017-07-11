# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Get virt-what information from the remote machine."""

import gettext

from ansible.module_utils import rho_cmd  # pylint: disable=no-name-in-module

T = gettext.translation('rho', 'locale', fallback=True)
_ = T.ugettext


# pylint: disable=too-few-public-methods
class VirtWhatRhoCmd(rho_cmd.RhoCmd):
    """This class wraps around the command string
    that is run to obtain information about
    virt-what i.e. virt-what.type.
    """

    def __init__(self):
        super(VirtWhatRhoCmd, self).__init__()

        self.name = "virt-what"

        self.fields = {'virt-what.type': _(
            "What type of virtualization"
            " a system is running,"""
            " as determined by virt-what")}

        self.cmd_names["virt_what"] = ['virt-what.type']

        cmd_string = "virt-what;echo $?"
        self.cmd_strings["virt_what"] = cmd_string

    def parse_data(self):
        """This method handles errors due to invalid results
        and populates the virt-what.type field accordingly.
        """
        if self.cmd_results[self.cmd_names.keys()[0]][1]:
            self.data['virt-what.type'] = 'error'
        elif self.cmd_results[self.cmd_names.keys()[0]][0]:
            results = [line for line in self.cmd_results[
                self.cmd_names.keys()[0]][0].strip().split('\n')]
            error = int(results[-1:][0])
            virt_what_output = results[:len(results) - 1]
            # pylint: disable=len-as-condition
            if error == 0:
                if len(virt_what_output) > 0:
                    # quote the results and join on
                    # ',' as virt-what can return multiple values
                    self.data['virt-what.type'] = '"%s"' % "," \
                        .join(virt_what_output)
                else:
                    self.data['virt-what.type'] = "bare metal"
