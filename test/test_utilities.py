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
            utilities.threaded_tailing(TMP_FOLLOW, utilities.tail_host_scan, 3)
            time.sleep(2)
            self.assertEqual(follow_list_out.getvalue(), 'follow\n')


class TestReadRanges(unittest.TestCase):

    def test_valid_ranges(self):
        range_list = ['10.10.181.9',
                      '10.10.128.[1:25]',
                      '10.10.[1:20].25',
                      '10.10.[1:20].[1:25]',
                      'localhost',
                      'mycentos.com',
                      'my-rhel[a:d].company.com',
                      'my-rhel[120:400].company.com']
        result = utilities.read_ranges(range_list)
        self.assertEqual(range_list, result)

    def test_invalid_ranges(self):
        range_list = ['10.10.[181.9',
                      '10.10.128.[a:25]',
                      '10.10.[1-20].25',
                      'my_rhel[a:d].company.com',
                      'my-rhel[a:400].company.com']
        with self.assertRaises(SystemExit):
            utilities.read_ranges(range_list)

    def test_issue404(self):
        range_list = ['10.1.1.1-10.1.1.254']
        with self.assertRaises(SystemExit):
            utilities.read_ranges(range_list)

    def test_cidr_range(self):
        range_list = ['192.168.124.0/25']
        self.assertEqual(
            utilities.read_ranges(range_list),
            ['192.168.124.[0:127]'])

    def test_invalid_file(self):
        range_list = ['/im/an/invalid/file']
        with self.assertRaises(SystemExit):
            utilities.read_ranges(range_list)


class TestCIDRToAnsible(unittest.TestCase):
    def test_wrong_format(self):
        with self.assertRaises(utilities.NotCIDRException):
            utilities.cidr_to_ansible('www.redhat.com')

    def test_extra_dots(self):
        with self.assertRaises(SystemExit):
            utilities.cidr_to_ansible('1.2..3.4/26')

    def test_octet_out_of_range(self):
        with self.assertRaises(SystemExit):
            utilities.cidr_to_ansible('1.2.3.256/12')

    def test_prefix_out_of_range(self):
        with self.assertRaises(SystemExit):
            utilities.cidr_to_ansible('1.2.3.4/33')

    def test_no_prefix(self):
        self.assertEqual(
            utilities.cidr_to_ansible('1.2.3.4/0'),
            '[0:255].[0:255].[0:255].[0:255]')

    def test_exact_ip(self):
        self.assertEqual(
            utilities.cidr_to_ansible('1.2.3.4/32'),
            '1.2.3.4')

    def test_first_octet(self):
        self.assertEqual(
            utilities.cidr_to_ansible('15.2.3.4/6'),
            '[12:15].[0:255].[0:255].[0:255]')

    def test_last_octet(self):
        self.assertEqual(
            utilities.cidr_to_ansible('1.2.3.4/30'),
            '1.2.3.[4:7]')

    def test_octet_boundary(self):
        self.assertEqual(
            utilities.cidr_to_ansible('1.2.3.4/16'),
            '1.2.[0:255].[0:255]')

    def test_beginning_of_octet(self):
        self.assertEqual(
            utilities.cidr_to_ansible('192.168.1.1/17'),
            '192.168.[0:127].[0:255]')

    def test_end_of_octet(self):
        self.assertEqual(
            utilities.cidr_to_ansible('192.168.1.1/23'),
            '192.168.[0:1].[0:255]')


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
