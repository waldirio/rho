# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Unit tests for library/spit_results.py."""

import os
import unittest
import mock
from library import spit_results

# pylint: disable=missing-docstring, no-self-use

TMP_TEST_REPORT = "/tmp/test_report.csv"


class TestSpitResults(unittest.TestCase):

    def setUp(self):
        if os.path.isfile(TMP_TEST_REPORT):
            os.remove(TMP_TEST_REPORT)

    @mock.patch("library.spit_results.AnsibleModule", autospec=True)
    def test__main__success(self, ansible_mod_cls):
        mod_obj = ansible_mod_cls.return_value
        pkg_line = """
        pciutils|3.5.1|2.el7|1500397509|Red Hat, Inc.|1491250625|
        x86-038.build.eng.bos.redhat.com|pciutils-3.5.1-2.el7.src.rpm|
        GPLv2+|Red Hat, Inc. <http://bugzilla.redhat.com/bugzilla>|
        Tue 18 Jul 2017 01:05:09 PM EDT|Mon 03 Apr 2017 04:17:05 PM EDT
        """
        args = {
            "name": "foo",
            "file_path": TMP_TEST_REPORT,
            "vals": [{'connection.uuid': '1',
                      'systemid.contents': '',
                      'redhat-packages.results': [pkg_line]}],
            "all_vars": {'host1':
                         {'fact1': 'value1',
                          'fact2': 'value2',
                          'res': {'fact3': 'value3'},
                          'connection': {'connection.uuid': '1'},
                          'jboss.jar-ver':
                          {'stdout_lines':
                           ['1.5.4.Final-redhat-1**2017-08-03']}}},
            "fact_names": ['fact1', 'connection.uuid',
                           'systemid.username',
                           'redhat-packages.last_built',
                           'jboss.deploy-dates', 'jboss.installed-versions']
        }
        mod_obj.params = args
        spit_results.main()
        expected_arguments_spec = {
            "name": {"required": True, "type": "str"},
            "file_path": {"required": True, "type": "str"},
            "vals": {"required": True, "type": "list"},
            "all_vars": {"required": True, "type": "dict"},
            "fact_names": {"required": True, "type": "list"}
        }

        assert(mock.call(argument_spec=expected_arguments_spec) ==
               ansible_mod_cls.call_args)
