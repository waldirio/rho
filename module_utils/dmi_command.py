# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Get BIOS information from the DMI."""

import gettext

from ansible.module_utils import rho_cmd  # pylint: disable=no-name-in-module

T = gettext.translation('rho', 'locale', fallback=True)
_ = T.ugettext


# pylint: disable=too-few-public-methods
class DmiRhoCmd(rho_cmd.RhoCmd):
    """This class wraps around all bios related
    command strings and currently maps the,
    one on one to 4 fields.
    """

    # note this test doesn't work well, or at all, for non root
    # users by default.

    def __init__(self):
        super(DmiRhoCmd, self).__init__()
        self.name = "dmi"

        self.fields = {'dmi.bios-vendor': _('BIOS vendor info from DMI'),
                       'dmi.bios-version': _('BIOS version info from DMI'),
                       'dmi.system-manufacturer': _(
                           'System manufacturer from DMI'),
                       'dmi.processor-family': _('Processor family from DMI')}

        self.cmd_names["bios_vendor"] = ['dmi.bios-vendor']
        self.cmd_names["bios_version"] = ['dmi.bios-version']
        self.cmd_names["bios_sys_manu"] = ['dmi.system-manufacturer']
        self.cmd_names["bios_processor_fam"] = ['dmi.processor-family']

        self.cmd_strings["bios_vendor"] = "/usr/sbin/dmidecode -s bios-vendor"
        self.cmd_strings["bios_version"] = "/usr/sbin/dmidecode " \
                                           "-s bios-version"
        self.cmd_strings["bios_sys_manu"] = (
            "/usr/sbin/dmidecode "
            "| grep -A4 'System Information' "
            "| grep 'Manufacturer' "
            "| sed -n -e 's/^.*Manufacturer:\\s//p'")
        self.cmd_strings["bios_processor_fam"] = "usr/sbin/dmidecode -s " \
                                                 "processor-family"

    def parse_data(self):
        """This method loops through all
        requested bios fields and parses
        the results and fills the data dictionary
        as required.
        """
        for k in self.cmd_names:
            if k in self.cmd_results.keys():
                if self.cmd_results[k][1]:
                    self.data[self.cmd_names[k][0]] = 'error'
                elif self.cmd_results[k][0]:
                    self.data[self.cmd_names[k][0]] = str.strip(
                        self.cmd_results[k][0])
