# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Check the redhat-release package on the remote machine."""

import gettext

from ansible.module_utils import rho_cmd  # pylint: disable=no-name-in-module

T = gettext.translation('rho', 'locale', fallback=True)
_ = T.ugettext


# pylint: disable=too-few-public-methods
class RedhatReleaseRhoCmd(rho_cmd.RhoCmd):
    """This class wraps around a single command string
    whose result is parsed to populate 4 possible
    fields, redhat-release.name, version and release.
    """

    def __init__(self):
        super(RedhatReleaseRhoCmd, self).__init__()
        self.name = "redhat-release"
        self.cmd_strings["get_release_info"] = 'rpm -q --queryformat ' \
                                               '"%{NAME}\n%{VERSION}' \
                                               '\n%{RELEASE}\n" ' \
                                               '--whatprovides' \
                                               ' redhat-release'
        self.cmd_names["get_release_info"] = ["redhat-release.name",
                                              "redhat-release.version",
                                              "redhat-release.release"]
        self.fields = {'redhat-release.name': _("name of"
                                                " package that "
                                                "provides 'red"
                                                "hat-release'"),
                       'redhat-release.version': _("version of "
                                                   "package that "
                                                   "provides 'red"
                                                   "hat-release'"),
                       'redhat-release.release': _("release of"
                                                   " package that "
                                                   "provides 'red"
                                                   "hat-release'")}

    def parse_data(self):
        """This method handles errors for invalid result
        and does simple parsing to obtain the three
        fields' info.
        """
        # new line seperated string, one result only
        if self.cmd_results["get_release_info"][1]:
            # and/or, something not dumb
            # pylint: disable=attribute-defined-outside-init
            self.data = {'redhat-release.name': 'error',
                         'redhat-release.version': 'error',
                         'redhat-release.release': 'error'}
            return
        fields = self.cmd_results["get_release_info"][0].splitlines()
        # no shell gives a single bogus line of output, we expect 3
        if len(fields) >= 3:
            self.data['redhat-release.name'] = fields[0].strip()
            self.data['redhat-release.version'] = fields[1].strip()
            self.data['redhat-release.release'] = fields[2].strip()
