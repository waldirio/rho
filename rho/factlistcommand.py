# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""List available facts."""

from __future__ import print_function

import re

from rho import utilities
from rho.clicommand import CliCommand
from rho.facts import FACT_DOCS
from rho.translation import _


# pylint: disable=too-few-public-methods
class FactListCommand(CliCommand):
    """List available facts."""

    def __init__(self):
        usage = _('usage: %prog fact list')
        shortdesc = _('list facts that rho can detect')
        desc = _('list facts that rho can detect. Filter fact names with '
                 '--filter <regex>')

        CliCommand.__init__(self, 'fact list', usage, shortdesc, desc)

        self.parser.add_option('--filter', dest='filter', metavar='filter',
                               help=_('regexp to filter facts - optional'))

    def _do_command(self):
        if self.options.filter:
            regexp = re.compile(self.options.filter)
        else:
            regexp = None

        for fact, desc in utilities.iteritems(FACT_DOCS):
            if not regexp or regexp.match(fact):
                print(fact, '-', desc)
