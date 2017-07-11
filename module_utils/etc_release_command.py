# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Read various /etc/*-release files."""

import subprocess as sp

from ansible.module_utils import rho_cmd  # pylint: disable=no-name-in-module


class EtcReleaseRhoCmd(rho_cmd.RhoCmd):
    """This class wraps around the command strings that
    get release information for boxes that contain
    non-Redhat packages installed in them. This wraps
    around a single command (which is an sh script)
    that 'echo's the name, version and release info
    (along with a boolean value)and this information
    is captured in the corresponding fields.
    """

    def __init__(self):
        super(EtcReleaseRhoCmd, self).__init__()

        self.name = "release"

        self.cmd_names["get_release_info"] = ["etc_release.name",
                                              "etc_release.version",
                                              "etc_release.release"]

        cmd_string = """if [ -f /etc/lsb-release ]; then
         . /etc/lsb-release
         os=$DISTRIB_ID
         ver=$DISTRIB_RELEASE
        elif [ -f /etc/debian_version ]; then
            os=Debian  # Or Ubuntu??
            ver=$( cat /etc/debian_version )
        elif [ -f /etc/redhat-release ]; then
            rel=$( cat /etc/redhat-release )
            boolean=1
        elif [ -f /etc/release ]; then
            rel=$( cat /etc/release )
            boolean=1
        elif [ -f /etc/SuSE-release ]; then
            rel=$( cat /etc/SuSE-release )
            boolean=1
        elif [ -f /etc/mandriva-release ]; then
            rel=$( cat /etc/mandriva-release )
            boolean=1
        elif [ -f /etc/enterprise-release ]; then
            rel=$( cat /etc/enterprise-release )
            boolean=1
        elif [ -f /etc/sun-release ]; then
            rel=$( cat /etc/sun-release )
            boolean=1
        elif [ -f /etc/slackware-release ]; then
            rel=$( cat /etc/slackware-release )
            boolean=1
        elif [ -f /etc/ovs-release ]; then
            rel=$( cat /etc/ovs-release )
            boolean=1
        elif [ -f /etc/arch-release ]; then
            rel=$( cat /etc/arch-release )
            boolean=1
        else
            os=$(uname -s)
            ver=$(uname -r)
        fi
        echo $boolean
        echo $os
        echo $ver
        echo $rel"""
        self.cmd_strings["get_release_info"] = cmd_string

    def run_cmd(self, facts):  # pylint: disable=unused-argument
        """The run_cmd method is overwritten for this
        class because of the additional requirement
        to parse the results according to the boolean
        value returned. A boolean value 1 means that
        the box contains redhat_release, SuSE-release
        mandriva-release, enterprise-release,
        sun-release, slackware-release, ovs-release, or
        arch-release and not 1 implies lsb-release,
        debian or for none of the above.

        :param facts: The facts to collect on the inventory
        """

        try:
            process_set = sp.Popen(self.cmd_strings["get_release_info"],
                                   shell=True, stdout=sp.PIPE,
                                   stderr=sp.PIPE)
            res = process_set.communicate()[0].split('\n')
            boolean = res[0].strip()
            if boolean == str(1):
                rel = res[3].strip()
                rel_list = rel.split('release')
                rel_name = rel_list[0].strip()
                rel_version = rel_list[1].strip()
                self.data['etc_release.name'] = rel_name
                self.data['etc_release.version'] = rel_version
                self.data['etc_release.release'] = rel.strip()
            else:
                os_name = res[1].strip()
                ver = res[2].strip()
                release = os_name + " " + ver
                self.data['etc_release.name'] = os_name
                self.data['etc_release.version'] = ver
                self.data['etc_release.release'] = release
        except OSError as err:
            rho_cmd.PRINT_LOG += "OSError >, " + str(err.errno) + "\n"
            rho_cmd.PRINT_LOG += "OSError > " + str(err.strerror) + "\n"
            rho_cmd.PRINT_LOG += "OSError > " + str(err.filename) + "\n"

    def parse_data(self):
        """Functionality for this method included in
        run_cmd.
        """
        pass
