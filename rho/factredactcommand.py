# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""redact sensitive facts."""

from __future__ import print_function

import csv
import sys
import os
import tempfile
from shutil import move
from optparse import SUPPRESS_HELP  # pylint: disable=deprecated-module
from rho import utilities
from rho.clicommand import CliCommand
from rho.translation import _
from rho.utilities import multi_arg, _read_in_file


# pylint: disable=too-few-public-methods
class FactRedactCommand(CliCommand):
    """Redact sensitive facts."""

    def __init__(self):
        usage = _('usage: %prog fact redact')
        shortdesc = _('redact facts from a report created by rho')
        desc = _('remove sensitive facts from report created by rho.')

        CliCommand.__init__(self, 'fact redact', usage, shortdesc, desc)

        self.parser.add_option("--reportfile", dest="report_path",
                               metavar="REPORTFILE",
                               help=_("Report file path - REQUIRED"))

        self.parser.add_option("--facts", dest="facts", metavar="FACTS",
                               action="callback", callback=multi_arg,
                               default=[], help=SUPPRESS_HELP)
        self.facts_to_redact = None

    def _validate_options(self):
        CliCommand._validate_options(self)

        if not self.options.report_path:
            print(_("No report location specified."))
            self.parser.print_help()
            sys.exit(1)

        normalized_path = os.path.normpath(self.options.report_path)
        if not os.path.isfile(normalized_path):
            print(_('Report location is invalid.'))
            sys.exit(1)

        # perform fact validation
        facts = self.options.facts
        if facts == [] or facts == ['default']:
            self.facts_to_redact = list(utilities.SENSITIVE_FACTS_TUPLE)
        elif os.path.isfile(facts[0]):
            self.facts_to_redact = _read_in_file(facts[0])
        else:
            assert isinstance(facts, list)
            self.facts_to_redact = facts
        # check facts_to_redact is subset of utilities.DEFAULT_FACTS
        all_facts = utilities.DEFAULT_FACTS
        facts_to_redact_set = set(self.facts_to_redact)
        if not facts_to_redact_set.issubset(all_facts):
            invalid_facts = facts_to_redact_set.difference(all_facts)
            print(_("Invalid facts were supplied to the command: " +
                    ",".join(invalid_facts)))
            self.parser.print_help()
            sys.exit(1)

    def _do_command(self):
        facts_not_found = set()
        facts_removed = set()
        data = []
        keys = None
        normalized_path = os.path.normpath(self.options.report_path)
        with open(normalized_path, 'r') as read_file:
            reader = csv.DictReader(read_file, delimiter=',')
            for row in reader:
                for fact in self.facts_to_redact:
                    if fact in row:
                        del row[fact]
                        facts_removed.add(fact)
                    else:
                        facts_not_found.add(fact)
                if keys is None:
                    keys = set(row.keys())
                data.append(row)

        for fact in facts_removed:
            print(_("Fact %s redacted" % fact))
        for fact in facts_not_found:
            print(_("Fact %s was not present in %s" %
                    (fact, self.options.report_path)))

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as data_temp:
            # Construct the CSV writer
            writer = csv.DictWriter(
                data_temp, fieldnames=sorted(keys), delimiter=',')

            # Write a CSV header if necessary
            writer.writeheader()

            # Write the data
            for row in data:
                writer.writerow(row)
        data_temp.close()
        move(data_temp.name, normalized_path)
