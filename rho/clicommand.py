#
# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

# pylint: disable=too-few-public-methods

""" Base CLI Command Class """

from __future__ import print_function
import logging
import sys
from optparse import OptionParser  # pylint: disable=deprecated-module
from rho.utilities import ensure_config_dir_exists, \
    ensure_data_dir_exists, RHO_LOG
from rho.translation import _


class CliCommand(object):

    """ Base class for all sub-commands. """
    def __init__(self, name="cli", usage=None, shortdesc=None,
                 description=None):

        self.shortdesc = shortdesc
        if shortdesc is not None and description is None:
            description = shortdesc
        self.parser = OptionParser(usage=usage, description=description)
        self.name = name
        self.passphrase = None
        self.args = None
        self.options = None
        self.verbosity = 0

        self.parser.add_option(
            "-v", dest="verbosity", action="count",
            help=_("Verbose mode. Use up to -vvvv for more verbosity."))

    def _validate_options(self):
        """
        Sub-commands can override to do any argument validation they
        require.
        """
        pass

    def _do_command(self):
        """
        Sub-commands define this method to perform the
        required action once all options have been verified.
        """
        pass

    def main(self):
        """
        The method that does a basic check for command
        validity and set's the process in motion.
        """

        (self.options, self.args) = self.parser.parse_args()

        # we dont need argv[0] in this list...

        self.args = self.args[1:]

        # Verbosity propagates in two ways to the individual commands:
        # first, as self.verbosity, and second, through the default
        # log level for the logging module. This means that other
        # modules can just use Python logging and it will work with
        # the verbosity by default.
        self.verbosity = self.options.verbosity
        if self.verbosity is None:
            log_level = logging.WARNING
        elif self.verbosity == 1:
            log_level = logging.INFO
        else:
            log_level = logging.DEBUG

        ensure_config_dir_exists()
        ensure_data_dir_exists()
        logging.basicConfig(filename=RHO_LOG, level=log_level)

        self._validate_options()

        if len(sys.argv) < 2:

            print(self.parser.error(_("Please enter at least 2 args")))

        # do the work, catch most common errors here:

        self._do_command()
