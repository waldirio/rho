# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Unit tests for rho/utilities.py."""

import unittest
from rho import utilities

# pylint: disable=missing-docstring


class TestValidatePort(unittest.TestCase):
    def test_wrong_type(self):
        with self.assertRaises(ValueError):
            utilities.validate_port([1, 2, 3])

    def test_unparseable_string(self):
        with self.assertRaises(ValueError):
            utilities.validate_port("abc")

    def test_negative_port(self):
        with self.assertRaises(ValueError):
            utilities.validate_port(-1)

    def test_too_large_port(self):
        with self.assertRaises(ValueError):
            utilities.validate_port(65536)

    def test_valid_string_port(self):
        self.assertEqual(utilities.validate_port("123"), 123)

    def test_valid_int_port(self):
        self.assertEqual(utilities.validate_port(123), 123)
