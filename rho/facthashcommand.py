# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Hash sensitive facts."""

from __future__ import print_function

import csv
import sys
import os
from optparse import SUPPRESS_HELP  # pylint: disable=deprecated-module
import hashlib
from rho import utilities
from rho.clicommand import CliCommand
from rho.translation import _
from rho.utilities import multi_arg, _read_in_file, write_csv_data


def compute_sha256_hash(input_string):
    """ Computes the sha256 hash for a string
    :param input_string: The string to hash
    :returns: The hex hash value
    """
    hasher = hashlib.sha256()
    hasher.update(input_string.encode('utf-8'))
    return hasher.hexdigest()


# pylint: disable=too-few-public-methods
class FactHashCommand(CliCommand):
    """Hash sensitive facts."""

    def __init__(self):
        usage = _('usage: %prog fact hash')
        shortdesc = _('hash facts within a report created by rho')
        desc = _('hash sensitive facts within a report created by rho.')

        CliCommand.__init__(self, 'fact hash', usage, shortdesc, desc)

        self.parser.add_option("--reportfile", dest="report_path",
                               metavar="REPORTFILE",
                               help=_("Report file path - REQUIRED"))

        self.parser.add_option("--facts", dest="facts", metavar="FACTS",
                               action="callback", callback=multi_arg,
                               default=[], help=SUPPRESS_HELP)

        self.parser.add_option("--outputfile", dest="hashed_path",
                               metavar="HASHEDPATH",
                               help=_("Location for the hashed file"),
                               default=None)

        self.facts_to_hash = None

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
            self.facts_to_hash = list(utilities.SENSITIVE_FACTS_TUPLE)
        elif os.path.isfile(facts[0]):
            self.facts_to_hash = _read_in_file(facts[0])
        else:
            assert isinstance(facts, list)
            self.facts_to_hash = facts
        # check facts_to_hash is subset of utilities.DEFAULT_FACTS
        all_facts = utilities.DEFAULT_FACTS
        facts_to_hash_set = set(self.facts_to_hash)
        if not facts_to_hash_set.issubset(all_facts):
            invalid_facts = facts_to_hash_set.difference(all_facts)
            print(_("Invalid facts were supplied to the command: " +
                    ",".join(invalid_facts)))
            self.parser.print_help()
            sys.exit(1)

    def read_and_hash(self, path):
        """ Read the given CSV file and hash the prescribed facts
        :param path: The csv file to read
        :returns: The keys (set) and data (dict) composing the csv file
        """
        facts_not_found = set()
        facts_hashed = set()
        data = []
        keys = None

        with open(path, 'r') as read_file:
            try:
                reader = csv.DictReader(read_file, delimiter=',')
                for row in reader:
                    for fact in self.facts_to_hash:
                        if fact in row:
                            row[fact] = compute_sha256_hash(row[fact])
                            facts_hashed.add(fact)
                        else:
                            facts_not_found.add(fact)
                    if keys is None:
                        keys = set(row.keys())
                    data.append(row)

                    for fact in facts_hashed:
                        print(_("Fact %s hashed" % fact))
                    for fact in facts_not_found:
                        print(_("Fact %s was not present in %s" %
                                (fact, self.options.report_path)))
            except csv.Error:
                print(_("An error occurred while attempting"
                        " to read CSV file %s." % (self.options.report_path)))
                sys.exit(1)

        return keys, data

    def _do_command(self):
        normalized_path = os.path.normpath(self.options.report_path)
        hashed_path = (self.options.hashed_path or normalized_path + '-hashed')

        keys, data = self.read_and_hash(normalized_path)
        write_csv_data(keys, data, hashed_path)
