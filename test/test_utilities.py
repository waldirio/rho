# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Unit tests for rho/utilities.py."""

import contextlib
import logging
import sys
import os
import time
import unittest
import six
from rho import utilities

# pylint: disable=missing-docstring
TMP_FOLLOW = "/tmp/follow.txt"


@contextlib.contextmanager
def redirect_stdout(stream):
    """Run a code block, capturing stdout to the given stream"""

    old_stdout = sys.stdout
    try:
        sys.stdout = stream
        yield
    finally:
        sys.stdout = old_stdout


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


class TestTailing(unittest.TestCase):
    def setUp(self):
        if os.path.isfile(TMP_FOLLOW):
            os.remove(TMP_FOLLOW)
        with open(TMP_FOLLOW, 'w') as follow_file:
            follow_file.write('follow\n')

    def test_threaded_tailing(self):
        follow_list_out = six.StringIO()
        with redirect_stdout(follow_list_out):
            utilities.threaded_tailing(TMP_FOLLOW, 3)
            time.sleep(2)
            self.assertEqual(follow_list_out.getvalue(), 'follow\n')


class TestRangeValidity(unittest.TestCase):

    def testcheck_range_validity(self):
        valid_range_list = ['10.10.181.9',
                            '10.10.128.[1:25]',
                            '10.10.[1:20].25',
                            '10.10.[1:20].[1:25]',
                            'localhost',
                            'mycentos.com',
                            'my-rhel[a:d].company.com',
                            'my-rhel[120:400].company.com']
        result = utilities.check_range_validity(valid_range_list)
        self.assertTrue(result)

    def testcheck_range_validity_error(self):
        valid_range_list = ['10.10.[181.9',
                            '10.10.128.[a:25]',
                            '10.10.[1-20].25',
                            'my_rhel[a:d].company.com',
                            'my-rhel[a:400].company.com']
        with self.assertRaises(SystemExit):
            utilities.check_range_validity(valid_range_list)

    def testcheck_range_cidr_error(self):
        valid_range_list = ['192.168.124.0/25']
        with self.assertRaises(SystemExit):
            utilities.check_range_validity(valid_range_list)


class TestSetupLogging(unittest.TestCase):
    def test_default_level(self):
        utilities.setup_logging(None)
        self.assertEqual(utilities.log.getEffectiveLevel(),
                         logging.WARNING)
        self.assertEqual(logging.getLogger().getEffectiveLevel(),
                         logging.WARNING)

    def test_verbose_level(self):
        utilities.setup_logging(2)
        self.assertEqual(utilities.log.getEffectiveLevel(),
                         logging.DEBUG)
        self.assertEqual(logging.getLogger().getEffectiveLevel(),
                         logging.WARNING)
