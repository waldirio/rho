#
# Based on sm-photo-tool cli.py: http://github.com/jmrodri/sm-photo-tool/
#
# Copyright (c) 2009 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

# pylint: disable=R0903, unused-import

""" Rho Command Line Interface """

from __future__ import print_function
import sys
import os
import inspect
import ansible
import rho
from rho.clicommand import CliCommand
from rho.authaddcommand import AuthAddCommand  # noqa
from rho.authclearcommand import AuthClearCommand  # noqa
from rho.autheditcommand import AuthEditCommand  # noqa
from rho.authlistcommand import AuthListCommand  # noqa
from rho.authshowcommand import AuthShowCommand  # noqa
from rho.factlistcommand import FactListCommand  # noqa
from rho.profileaddcommand import ProfileAddCommand  # noqa
from rho.profileclearcommand import ProfileClearCommand  # noqa
from rho.profileeditcommand import ProfileEditCommand  # noqa
from rho.profilelistcommand import ProfileListCommand  # noqa
from rho.profileshowcommand import ProfileShowCommand  # noqa
from rho.scancommand import ScanCommand  # noqa


class CLI(object):
    """Class responsible for displaying ussage or matching inputs
    to the valid set of commands supported by rho.
    """
    def __init__(self):
        self.cli_commands = {}
        # pylint: disable=unused-variable
        for name, clazz in inspect.getmembers(sys.modules[__name__]):
            if inspect.isclass(clazz):
                if isinstance(clazz, type) and  \
                        issubclass(clazz, CliCommand):
                    cmd = clazz()
                    # ignore the base class
                    if cmd.name != "cli":
                        self.cli_commands[cmd.name] = cmd

    def _add_command(self, cmd):
        """Add a command to the valid commands list
        :param cmd: The command to add to the valid command list
        """
        self.cli_commands[cmd.name] = cmd

    def _usage(self):
        """rho command lines usage command to supply basic help information.
        Supplys list of commands and a short description
        """
        print("\nUsage: %s [options] MODULENAME --help\n" %
              (os.path.basename(sys.argv[0])))
        print("Supported modules:\n")

        # want the output sorted
        items = sorted(self.cli_commands.items())
        for (name, cmd) in items:
            print("\t%-14s %-25s" % (name, cmd.shortdesc))
        print("")

    def _find_best_match(self, args):
        """
        Returns the subcommand class that best matches the subcommand specified
        in the argument list. For example, if you have two commands that start
        with auth, 'auth show' and 'auth'. Passing in auth show will match
        'auth show' not auth. If there is no 'auth show', it tries to find
        'auth'.

        This function ignores the arguments which begin with --
        :param args: The command line arguments
        :returns: The matched command or None
        """
        possiblecmd = []
        for arg in args[1:]:
            if not arg.startswith("-"):
                possiblecmd.append(arg)

        if not possiblecmd:
            return None

        cmd = None
        key = " ".join(possiblecmd)
        if " ".join(possiblecmd) in self.cli_commands:
            cmd = self.cli_commands[key]

        i = -1
        while cmd is None:
            key = " ".join(possiblecmd[:i])
            if key is None or key == "":
                break

            if key in self.cli_commands:
                cmd = self.cli_commands[key]
            i -= 1

        return cmd

    def main(self):
        """Method determine whether to display usage or pass input
        to find the best command match. If no match is found the
        usage is displayed
        """
        len_sys_argv = len(sys.argv)
        if len_sys_argv < 2 or not self._find_best_match(sys.argv):
            if len_sys_argv == 2 and sys.argv[1] == '--help':
                self._usage()
                sys.exit(0)
            elif len_sys_argv == 2 and sys.argv[1] == '--version':
                print('version: ' + rho.__version__)
                print('\tansible: ' + ansible.__version__)
                print('\tpython: ' + sys.version)
                sys.exit(0)
            else:
                self._usage()
                sys.exit(1)

        cmd = self._find_best_match(sys.argv)
        if not cmd:
            self._usage()
            sys.exit(1)

        cmd.main()
