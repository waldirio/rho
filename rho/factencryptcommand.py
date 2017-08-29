# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Encrypt sensitive facts."""

from __future__ import print_function

import csv
import sys
import os
from optparse import SUPPRESS_HELP  # pylint: disable=deprecated-module
from rho import utilities
from rho.clicommand import CliCommand
from rho.translation import _
from rho.utilities import multi_arg, _read_in_file, write_csv_data
from rho.vault import get_vault

PROMPT = "Please enter your encryption password: "


# pylint: disable=too-few-public-methods
class FactEncryptCommand(CliCommand):
    """Encrypt sensitive facts."""

    def __init__(self):
        usage = _('usage: %prog fact encrypt')
        shortdesc = _('encrypt facts within a report created by rho')
        desc = _('encrypt sensitive facts within a report created by rho.')

        CliCommand.__init__(self, 'fact encrypt', usage, shortdesc, desc)

        self.parser.add_option("--reportfile", dest="report_path",
                               metavar="REPORTFILE",
                               help=_("Report file path - REQUIRED"))

        self.parser.add_option("--facts", dest="facts", metavar="FACTS",
                               action="callback", callback=multi_arg,
                               default=[], help=SUPPRESS_HELP)
        self.facts_to_encrypt = None

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
            self.facts_to_encrypt = list(utilities.SENSITIVE_FACTS_TUPLE)
        elif os.path.isfile(facts[0]):
            self.facts_to_encrypt = _read_in_file(facts[0])
        else:
            assert isinstance(facts, list)
            self.facts_to_encrypt = facts
        # check facts_to_encrypt is subset of utilities.DEFAULT_FACTS
        all_facts = utilities.DEFAULT_FACTS
        facts_to_encrypt_set = set(self.facts_to_encrypt)
        if not facts_to_encrypt_set.issubset(all_facts):
            invalid_facts = facts_to_encrypt_set.difference(all_facts)
            print(_("Invalid facts were supplied to the command: " +
                    ",".join(invalid_facts)))
            self.parser.print_help()
            sys.exit(1)

    def read_and_encrypt(self, path, vault):
        """ Read the given CSV file and encrypt the prescribed facts
        utilizing the given password.
        :param path: The csv file to read
        :returns: The keys (set) and data (dict) composing the csv file
        """
        facts_not_found = set()
        facts_encrypted = set()
        data = []
        keys = None

        with open(path, 'r') as read_file:
            reader = csv.DictReader(read_file, delimiter=',')
            for row in reader:
                for fact in self.facts_to_encrypt:
                    if fact in row:
                        row[fact] = vault.dump(row[fact])
                        facts_encrypted.add(fact)
                    else:
                        facts_not_found.add(fact)
                if keys is None:
                    keys = set(row.keys())
                data.append(row)

                for fact in facts_encrypted:
                    print(_("Fact %s encrypted" % fact))
                for fact in facts_not_found:
                    print(_("Fact %s was not present in %s" %
                            (fact, self.options.report_path)))

        return keys, data

    def _do_command(self):
        vault = get_vault(prompt=PROMPT)
        normalized_path = os.path.normpath(self.options.report_path)
        keys, data = self.read_and_encrypt(normalized_path, vault)
        write_csv_data(keys, data, normalized_path)
