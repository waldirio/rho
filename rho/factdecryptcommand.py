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

PROMPT = "Please enter your decryption password: "


# pylint: disable=too-few-public-methods
class FactDecryptCommand(CliCommand):
    """Decrypt sensitive facts."""

    def __init__(self):
        usage = _('usage: %prog fact decrypt')
        shortdesc = _('decrypt facts within a report created by rho')
        desc = _('decrypt sensitive facts within a report created by rho.')

        CliCommand.__init__(self, 'fact decrypt', usage, shortdesc, desc)

        self.parser.add_option("--reportfile", dest="report_path",
                               metavar="REPORTFILE",
                               help=_("Report file path - REQUIRED"))

        self.parser.add_option("--facts", dest="facts", metavar="FACTS",
                               action="callback", callback=multi_arg,
                               default=[], help=SUPPRESS_HELP)
        self.facts_to_decrypt = None

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
            self.facts_to_decrypt = list(utilities.SENSITIVE_FACTS_TUPLE)
        elif os.path.isfile(facts[0]):
            self.facts_to_decrypt = _read_in_file(facts[0])
        else:
            assert isinstance(facts, list)
            self.facts_to_decrypt = facts
        # check facts_to_decrypt is subset of utilities.DEFAULT_FACTS_TUPLE
        all_facts = utilities.DEFAULT_FACTS_TUPLE
        facts_to_decrypt_set = set(self.facts_to_decrypt)
        if not facts_to_decrypt_set.issubset(all_facts):
            invalid_facts = facts_to_decrypt_set.difference(all_facts)
            print(_("Invalid facts were supplied to the command: " +
                    ",".join(invalid_facts)))
            self.parser.print_help()
            sys.exit(1)

    def read_and_decrypt(self, path, vault):
        """ Read the given CSV file and decrypt the prescribed facts
        utilizing the given password.
        :param path: The csv file to read
        :returns: The keys (set) and data (dict) composing the csv file
        """
        facts_not_found = set()
        facts_decrypted = set()
        data = []
        keys = None

        with open(path, 'r') as read_file:
            reader = csv.DictReader(read_file, delimiter=',')
            for row in reader:
                for fact in self.facts_to_decrypt:
                    if fact in row:
                        row[fact] = vault.load(row[fact])
                        facts_decrypted.add(fact)
                    else:
                        facts_not_found.add(fact)
                if keys is None:
                    keys = set(row.keys())
                data.append(row)

                for fact in facts_decrypted:
                    print(_("Fact %s decrypted" % fact))
                for fact in facts_not_found:
                    print(_("Fact %s was not present in %s" %
                            (fact, self.options.report_path)))

        return keys, data

    def _do_command(self):
        vault = get_vault(prompt=PROMPT)
        normalized_path = os.path.normpath(self.options.report_path)
        keys, data = self.read_and_decrypt(normalized_path, vault)
        write_csv_data(keys, data, normalized_path)
