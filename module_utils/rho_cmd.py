# Copyright (c) 2009-2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""RhoCmd: a base class with common functionality for our Ansible modules."""

import subprocess as sp

PRINT_LOG = ""


class RhoCmd(object):
    """RhoCmd and its sub-classes are wrapper classes around
    the cli cmds we run on the host machines. The
    rho_cmd class will have five dictionaries.
    """

    # The cmd_names dictionary maps all the commands that are associated
    # with the class to the corresponding fields(facts) requested.
    # The cmd_strings dictionary maps each command name to the
    # actual command string that is run in the cli. The results
    # so obtained are stored in the cmd_results dictionary whose
    # keys are the command names. The fields dictionary stores
    # the localized versions of the field names and the data
    # dictionary is responsible for storing all the facts collected
    # from all the classes ever invoked.

    def __init__(self):
        self.cmd_results = {}
        self.data = {}
        self.cmd_strings = {}
        self.cmd_names = {}
        self.name = "cmd_name"

    def run_cmd(self, facts):
        """run_cmd is what runs the command strings associated
        to corresponding facts in cli of the host boxes. It
        accepts an input variable 'facts' which can either be
        'all' or a list of facts the user wants to collect
        associated with the particular RhoCmd. Passing in
        'all' would run all the command strings associated
        with the RhoCmd thereby collecting all facts. Passing
        in a list of facts would make the method run only
        the command strings related to those facts.

        :param facts: The facts to collect on inventory machines
        """
        global PRINT_LOG  # pylint: disable=global-statement

        if not self.cmd_names:
            PRINT_LOG += "RhoCmd has undefined 'cmd_names' \n"
            return

        if not self.cmd_strings:
            PRINT_LOG += "RhoCmd has undefined 'cmd_strings' \n"
            return

        requested_cmd_names = []

        if isinstance(facts, list):
            for fact in facts:
                for cmd_name in self.cmd_names:
                    if fact in self.cmd_names[cmd_name]:
                        requested_cmd_names.append(cmd_name)

        elif isinstance(facts, str):
            if facts == 'all':
                requested_cmd_names = self.cmd_names.keys()
            else:
                PRINT_LOG += "Invalid string for 'facts'." \
                             " Only permitted string " \
                             "is 'all'. \n"
                return
        else:
            PRINT_LOG += "Invalid input for facts. Acceptable" \
                         " inputs are the string 'all' or a " \
                         "list of strings (one for each fact) \n"
            return

        for cmd_name in requested_cmd_names:
            cmd_string = self.cmd_strings[cmd_name]
            try:
                process = sp.Popen(cmd_string, shell=True,
                                   stdout=sp.PIPE, stderr=sp.PIPE)
                out, err = process.communicate()
                self.cmd_results[cmd_name] = (out, err)
            except OSError as ex:
                PRINT_LOG += "OSError >, " + str(ex.errno) + "\n"
                PRINT_LOG += "OSError > " + str(ex.strerror) + "\n"
                PRINT_LOG += "OSError > " + str(ex.filename) + "\n"

        self.parse_data()

    def parse_data(self):
        """Used to parse the information collected from cli
        in order to fill in the appropriate values in
        the data dictionary of a RhoCmd. Defined in
        sub-class since data collected from cli differs
        according to the command_string run. This method
        has been documented according to sub-class
        specifics.

        :raises NotImplementedError: raises an exception
        """
        raise NotImplementedError
