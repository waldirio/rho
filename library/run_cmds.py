#!/usr/bin/python
# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

# pylint: disable=too-few-public-methods, too-many-lines, fixme

"""Commands to run on machines"""

import json

import ast
# pylint:disable=no-name-in-module
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import rho_cmd
from ansible.module_utils import date_command
from ansible.module_utils import uname_command
from ansible.module_utils import subman_facts_command
from ansible.module_utils import redhat_packages_command
from ansible.module_utils import redhat_release_command
from ansible.module_utils import etc_release_command
from ansible.module_utils import cpu_command
from ansible.module_utils import file_commands
from ansible.module_utils import dmi_command
from ansible.module_utils import virt_what_command
from ansible.module_utils import virt_command

# List of default commands
DEFAULT_CMDS = [uname_command.UnameRhoCmd,
                redhat_release_command.RedhatReleaseRhoCmd,
                file_commands.InstnumRhoCmd,
                file_commands.SystemIdRhoCmd,
                cpu_command.CpuRhoCmd,
                etc_release_command.EtcReleaseRhoCmd,
                file_commands.EtcIssueRhoCmd,
                dmi_command.DmiRhoCmd,
                virt_command.VirtRhoCmd,
                redhat_packages_command.RedhatPackagesRhoCmd,
                virt_what_command.VirtWhatRhoCmd,
                date_command.DateRhoCmd,
                subman_facts_command.SubmanFactsRhoCmd]

# Dictionary mapping class keywords
# passed in through the playbook (attached
# to the field requested using an '_').

DEFAULT_CMD_DICT = {"Username": uname_command.UnameRhoCmd,
                    "RedhatRelease":
                    redhat_release_command.RedhatReleaseRhoCmd,
                    "Instnum": file_commands.InstnumRhoCmd,
                    "SysId": file_commands.SystemIdRhoCmd,
                    "Cpu": cpu_command.CpuRhoCmd,
                    "EtcRelease": etc_release_command.EtcReleaseRhoCmd,
                    "EtcIssue": file_commands.EtcIssueRhoCmd,
                    "Dmi": dmi_command.DmiRhoCmd,
                    "Virt": virt_command.VirtRhoCmd,
                    "RedhatPackages":
                    redhat_packages_command.RedhatPackagesRhoCmd,
                    "VirtWhat": virt_what_command.VirtWhatRhoCmd,
                    "Date": date_command.DateRhoCmd,
                    "SubmanFacts": subman_facts_command.SubmanFactsRhoCmd}


class RunCommands(object):
    """Class that contains the functionality to
    parse the inputs from the playbook and stores
    the requested facts in an instance variable
    called 'facts_requested'.
    """

    def __init__(self, module):
        self.name = module.params["name"]
        self.facts_requested = {}

        # exception used to see if the input from playbook
        # is a list of facts or just a string so that
        # it can be converted to python data structures
        # as suited.

        try:
            self.fact_names = ast.literal_eval(module.params["fact_names"])
        except:  # pylint: disable=bare-except
            self.fact_names = module.params["fact_names"]

        # Split each requested fact on the first '_' so as to obtain
        # the RhoCmd sub-class that's being requested and store the
        # string to the right of '_' as one of the facts requested
        # for that respective rho command class (so the class knows)
        # which command strings to run by using the two dictionaries,
        # cmd_strings and cmd_names. Of course, this is only valid
        # when the input is in the form of a list of fact_names.

        if isinstance(self.fact_names, list):
            for f_name in self.fact_names:
                f_name_list = f_name.strip().split('_', 1)
                command = DEFAULT_CMD_DICT[f_name_list[0]]
                fact = f_name_list[1]
                if command in DEFAULT_CMDS:
                    if command in self.facts_requested.keys():
                        self.facts_requested[command].append(fact)
                    else:
                        self.facts_requested[command] = [fact]

                    # If type of input is a string then the only allowed,
                    # string is 'default' which means the user has requested
                    # all RhoCmds subclasses and all of their cmd strings will
                    # be run to fill in all corresponding fields.

        elif isinstance(self.fact_names, str):
            if self.fact_names.lower().strip() == "default":
                for def_cmd in DEFAULT_CMDS:
                    self.facts_requested[def_cmd] = "all"
            else:
                rho_cmd.PRINT_LOG += "FACT NOT AVAILABLE. EXITING \n"
                return
        else:
            rho_cmd.PRINT_LOG += "INVALID FACT TYPE. EXITING \n"
            return

    def execute_commands(self):
        """Method that creates instances of all RhoCmd subclasses
        requested in the playbook and runs the command strings
        desired to get the corresponding fields information.
        """
        # Goes through all the default commands
        # and executes them on the box's shell
        info_dict = {}
        for command in self.facts_requested:
            rcmd = command()
            rcmd.run_cmd(self.facts_requested[command])
            info_dict.update(rcmd.data)

        if 'all' not in self.facts_requested.values():

            # list that stores out the flattened out
            # values list of the facts_requested dictionary
            # to keep track of all fields requested so
            # that only those can be reported.

            facts_requested_list = [item
                                    for sublist
                                    in self.facts_requested.values()
                                    for item in sublist]

            if 'all' not in facts_requested_list:
                for k in info_dict:
                    if k not in facts_requested_list:
                        info_dict.pop(k, None)

        return info_dict


def main():
    """Creates an instance of an AnsibleModule that grabs information
    from the playbook about the facts that need to be collected.
    """
    module = AnsibleModule(argument_spec=dict(name=dict(required=True),
                                              fact_names=dict(required=False)))

    try:
        my_runner = RunCommands(module=module)
        info_dict = my_runner.execute_commands()
        response = json.dumps(info_dict)
        module.exit_json(changed=False, meta=response)
    except OSError:
        module.exit_json(changed=False, meta=rho_cmd.PRINT_LOG)


if __name__ == '__main__':
    main()
