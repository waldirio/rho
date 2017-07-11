# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Get /proc/cpuinfo information from the remote machine."""

import gettext
import re
import subprocess as sp

from ansible.module_utils import rho_cmd  # pylint:disable=no-name-in-module

T = gettext.translation('rho', 'locale', fallback=True)
_ = T.ugettext


class CpuRhoCmd(rho_cmd.RhoCmd):
    """This class wraps around just one
    command string when run gives a
    result this is parsed to fill
    8 fields.
    """

    def __init__(self):
        super(CpuRhoCmd, self).__init__()

        self.name = "cpu"

        self.cmd_names["get_cpu_info"] = ["cpu.count",
                                          "cpu.socket_count",
                                          "cpu.vendor_id",
                                          "cpu.bogomips",
                                          "cpu.cpu_family",
                                          "cpu.model_name",
                                          "cpu.model_ver"]

        self.cmd_strings["get_cpu_info"] = "cat /proc/cpuinfo"

        self.fields = {'cpu.count': _('number of processors'),
                       'cpu.socket_count': _('number of sockets'),
                       'cpu.vendor_id': _("cpu vendor name"),
                       'cpu.bogomips': _("bogomips"),
                       'cpu.cpu_family': _("cpu family"),
                       'cpu.model_name': _("name of cpu model"),
                       'cpu.model_ver': _("cpu model version")}

    def parse_data(self):
        # pylint: disable=missing-docstring, attribute-defined-outside-init
        self.data = self.parse_data_cpu(self.cmd_results)

    # pylint: disable=no-self-use
    def parse_data_cpu(self, results):
        """Helper method to parse results related
        to CpuRhoCmd and it's sub-classes. It runs
        a subprocess to run the command to obtain
        dmidecode information which is required
        for populating the cpu_socket count field.
        Creates a dictionary cpu_dict to store
        specific information which is later recorded
        into the data dictionary for the csv.

        :param results: The collected cpu results
        :return: updated cpu dataset
        """
        data = {}
        cpu_count = 0
        process = sp.Popen("/usr/sbin/dmidecode -t 4",
                           shell=True,
                           stdout=sp.PIPE,
                           stderr=sp.PIPE)
        dmidecode = process.communicate()
        for line in results["get_cpu_info"][0].splitlines():
            if line.find("processor") == 0:
                cpu_count += 1
        data["cpu.count"] = cpu_count
        data['cpu.socket_count'] = dmidecode[1].\
            replace('\n', '').replace('\r', '') \
            if dmidecode[1] else \
            len(re.findall('Socket Designation', dmidecode[0]))

        cpu_dict = {}
        for line in results["get_cpu_info"][0].splitlines():
            # first blank line should be end of first cpu
            # for this case, we are only grabbing the fields from the first
            # cpu and the total count. Should be close enough.
            if line == "":
                break
            parts = line.split(':')
            # should'nt be ':', but just in case, join all parts and strip
            cpu_dict[parts[0].strip()] = ("".join(parts[1:])).strip()

        # we don't need everything, just parse out the interesting bits

        # This only supports i386/x86_64. We could add support for more
        # but it's a lot of ugly code (see read_cpuinfo() in smolt.py
        # from smolt[I know it's ugly, I wrote it...]) That code also
        # needs the value of uname() available to it, which we don't
        #  currently have a way of plumbing in. So
        # x86* only for now... -akl
        # empty bits to return if we are on say, ia64
        data.update({'cpu.vendor_id': '',
                     'cpu.model_name': '',
                     'cpu.bogomips': '',
                     'cpu.cpu_family': '',
                     'cpu.model_ver': ''})

        try:
            data["cpu.vendor_id"] = cpu_dict.get("vendor_id")
            # model name should help find kvm/qemu guests...
            data["cpu.model_name"] = cpu_dict.get("model name")
            # they would take my linux card away if I didn't include bogomips
            data["cpu.bogomips"] = cpu_dict.get("bogomips")
            data["cpu.cpu_family"] = cpu_dict.get("cpu family")
            data["cpu.model_ver"] = cpu_dict.get("model")
        except:  # pylint: disable=bare-except
            pass

        return data
