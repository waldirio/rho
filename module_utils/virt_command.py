# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Try to determine if the remote machine is a virtualization guest or host."""

import gettext

# pylint: disable=no-name-in-module
from ansible.module_utils import cpu_command

T = gettext.translation('rho', 'locale', fallback=True)
_ = T.ugettext


# pylint: disable=too-few-public-methods
class VirtRhoCmd(cpu_command.CpuRhoCmd):
    """This class wraps around the command strings
    to get information for fields like sys_manu,
    xen_guest etc (currently 6 in total).
    """

    # try to determine if we are a virt guest, a host, or bare metal

    def __init__(self):
        super(VirtRhoCmd, self).__init__()
        self.name = 'VirtRhoCmd'

        self.fields = {'virt.virt': _("If a host is a virt guest,"
                                      " host, or bare metal"),
                       'virt.type': _("What type of virtualization"
                                      " a system is running"),
                       'virt.num_guests': _("The number of "
                                            "virtualized guests"),
                       'virt.num_running_guests': _("The number"
                                                    " of running"
                                                    "virtualized "
                                                    "guests")}

        cmd_template = "if [ -e %s ] ;" \
                       " then echo \"true\"; else echo \"false\"; fi"

        self.cmd_names["sys_manu"] = ["virt.virt", "virt.type"]
        self.cmd_names["xen_guest"] = ["virt.virt", "virt.type"]
        self.cmd_names["privcmd"] = ["virt.virt", "virt.type"]
        self.cmd_names["kvm"] = ["virt.virt", "virt.type"]
        self.cmd_names["virt_all_list"] = ["virt.num_guests"]
        self.cmd_names["virt_running_list"] = ["virt.num_running_guests"]

        self.cmd_strings["sys_manu"] = (
            "/usr/sbin/dmidecode "
            "| grep -A4 'System Information' "
            "| grep 'Manufacturer' "
            "| sed -n -e 's/^.*Manufacturer:\\s//p'")
        self.cmd_strings["xen_guest"] = "ps aux | grep xend | grep -v grep"
        self.cmd_strings["privcmd"] = cmd_template % "/proc/xen/privcmd"
        self.cmd_strings["kvm"] = cmd_template % "/dev/kvm"
        self.cmd_strings["virt_all_list"] = "virsh -c qemu" \
                                            ":///system --readonly" \
                                            " list --all"
        self.cmd_strings["virt_running_list"] = "virsh -c qemu:///" \
                                                "system --readonly " \
                                                "list --uuid"

    def parse_data(self):
        """Parse results of command strings
        for all required fields.
        """
        self.data["virt.virt"] = ""
        self.data["virt.type"] = ""

        # calculate number of guests
        self._num_guests()

        # calculate number of running guests
        self._num_running_guests()

        # check /proc/cpuinfo to see if we are Qemu/kvm
        self._check_cpuinfo_for_qemu()

        self._check_for_dev_kvm()
        # run dmidecode again, see what system-manufacturer is and
        # and if know it (also, check to see if dmidecode fails, like it
        # will for non root)
        self._check_dmidecode()
        # look for xen files (proc/xen/privcmd, /proc/xen/capabilities)
        #
        self._check_for_xen()
        # see if we are running xend...
        self._check_for_xend()

    # We are going to try a variety of hacks and kluges to see if we are virt,
    # and if so, what kind. Mainly looking for xen/kvm here, but if anything
    # else is easy to detect, try that too.

    # based heavily on "virt-what" and facters virt detections
    # can't use virt-what since it's not on most systems
    # it's also relys on root access...

    def _check_cpuinfo_for_qemu(self):
        # look at model name of /proc/cpuinfo
        data = self.parse_data_cpu(self.cmd_results)
        # model_name can be an empty string...
        if data["cpu.model_name"] and data["cpu.model_name"][:4] == "QEMU":
            # hmm, it could be regular old qemu here, but
            # this is probably close enough for reporting
            self.data["virt.type"] = "kvm"
            self.data["virt.virt"] = "virt-guest"
            return True
        return False

    def _check_for_dev_kvm(self):
        if "kvm" in self.cmd_results.keys():
            if self.cmd_results["kvm"][1]:
                self.data["virt.type"] = 'error'
                self.data["virt.virt"] = 'error'
            elif self.cmd_results["kvm"][0]:
                dev_kvm = str.strip(self.cmd_results["kvm"][0])
                if dev_kvm == "true":
                    self.data["virt.type"] = "kvm"
                    self.data["virt.virt"] = "virt-host"
                else:
                    self.data["virt.type"] = "error: not kvm"
                    self.data["virt.virt"] = "error: not kvm"

    # look at the results of dmidecode for hints about what type of
    # virt we have. could probably also track vmware esx version with
    # bios version. None of this works as non root, so it's going to
    # fail most of the time.

    def _check_dmidecode(self):
        if "sys_manu" in self.cmd_results.keys():
            if self.cmd_results["sys_manu"][1]:
                self.data["virt.type"] = 'error'
                self.data["virt.virt"] = 'error'
            elif self.cmd_results["sys_manu"][0]:
                manuf = str.strip(self.cmd_results["sys_manu"][0])
                if manuf:
                    if manuf.find("VMware") > -1:
                        self.data["virt.type"] = "vmware"
                        self.data["virt.virt"] = "virt-guest"

                    if manuf.find("innotek GmbH") > -1:
                        self.data["virt.type"] = "virtualbox"
                        self.data["virt.virt"] = "virt-guest"

                    if manuf.find("Microsoft") > -1:
                        self.data["virt.type"] = "virtualpc"
                        self.data["virt.virt"] = "virt-guest"

                    if manuf.find("QEMU") > -1:
                        self.data["virt.type"] = "kvm"
                        self.data["virt.virt"] = "virt-guest"

    def _check_for_xend(self):
        # It would be way cooler if we could poke the cpuid and see if
        # is a xen guest, but that requires a util to do it, and root
        #
        if "xen_guest" in self.cmd_results.keys():
            if self.cmd_results["xen_guest"][1]:
                self.data["virt.type"] = "error"
                self.data["virt.virt"] = "error"
            if self.cmd_results["xen_guest"][0]:
                # is xend running? must be a xen host
                # ugly...
                self.data["virt.type"] = "xen"
                self.data["virt.virt"] = "virt-host"

    def _check_for_xen(self):
        # look for /proc/xen/privcmd
        # Note: xen show "qemu" as cputype as well, so we do this
        # after looking at cpuinfo
        if "privcmd" in self.cmd_results.keys():
            if self.cmd_results["privcmd"][1]:
                self.data["virt.type"] = 'error'
                self.data["virt.virt"] = 'error'
            elif self.cmd_results["privcmd"][0]:
                if str.strip(self.cmd_results["privcmd"][0]) == "true":
                    self.data["virt.type"] = "xen"
                    self.data["virt.virt"] = "virt-guest"
                else:
                    self.data["virt.type"] = "error: privcmd false"
                    self.data["virt.virt"] = "error: privcmd false"

    def _num_guests(self):
        if "virt_all_list" in self.cmd_results.keys():
            if self.cmd_results["virt_all_list"][1]:
                self.data["virt.num_guests"] = 'error'
            elif self.cmd_results["virt_all_list"][0]:
                # we want to remove the title and
                # seperator lines of virsh output
                output = self.cmd_results["virt_all_list"][0].strip().split(
                    '\n')[2:]
                if not output:
                    self.data["virt.num_guests"] = 0
                self.data["virt.num_guests"] = len(output)

    def _num_running_guests(self):
        if "virt_running_list" in self.cmd_results.keys():
            if self.cmd_results["virt_running_list"][1]:
                self.data['virt.num_running_guests'] = 'error'
            elif self.cmd_results["virt_running_list"][0]:
                self.data['virt.num_running_guests'] = \
                    len(self.cmd_results["virt_running_list"][0].strip())
            else:
                self.data['virt.num_running_guests'] = 0
