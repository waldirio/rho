# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Test the rho.facts module."""

import unittest

from rho import facts


class TestFacts(unittest.TestCase):
    """Tests for rho.facts."""

    def setUp(self):
        self.category = set()

        facts.new_fact('fact1', 'test fact 1', True,
                       is_sensitive=True,
                       always_collect=True)

        facts.new_fact('fact2', 'test fact 2', False,
                       is_sensitive=False,
                       always_collect=False,
                       categories=[self.category])

    def test_new_fact(self):
        """Basic tests for facts.new_fact."""

        self.assertIn('fact1', facts.ALL_FACTS)
        self.assertIn('fact1', facts.SENSITIVE_FACTS)
        self.assertIn('fact1', facts.DEFAULT_FACTS)
        self.assertIn('fact1', facts.ALWAYS_COLLECT)
        self.assertNotIn('fact1', self.category)

        self.assertIn('fact2', facts.ALL_FACTS)
        self.assertNotIn('fact2', facts.SENSITIVE_FACTS)
        self.assertNotIn('fact2', facts.DEFAULT_FACTS)
        self.assertNotIn('fact2', facts.ALWAYS_COLLECT)
        self.assertIn('fact2', self.category)

    def test_expand_facts_all(self):
        """Make sure expand_facts expands 'all'"""

        self.assertEqual(facts.expand_facts(['all', 'fact1', 'fact2']),
                         facts.ALL_FACTS)

    def test_expand_facts_default(self):
        """Make sure the default is DEFAULT_FACTS."""

        self.assertEqual(facts.expand_facts(['default']),
                         facts.DEFAULT_FACTS)

    def test_default_with_extras(self):
        """Make sure extra facts are preserved when expanding fact sets."""

        expanded = facts.expand_facts(['default', 'fact1', 'fact2'])
        self.assertTrue(facts.DEFAULT_FACTS.issubset(expanded))
        self.assertIn('fact1', expanded)
        self.assertIn('fact2', expanded)

    def test_expand_facts_basic(self):
        """Basic functionality of expand_facts."""

        expanded = facts.expand_facts(['fact1', 'fact2'])
        self.assertIn('fact1', expanded)
        self.assertIn('fact2', expanded)
        self.assertTrue(facts.ALWAYS_COLLECT.issubset(expanded))

    def test_expand_facts_no_facts(self):
        """Make sure expand_facts works with no facts supplied."""

        self.assertEqual(facts.expand_facts([]),
                         facts.DEFAULT_FACTS)


if __name__ == '__main__':
    unittest.main()
