#
# Copyright (c) 2009 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

# pylint: disable=R0903

"""Module responsible for displaying results of rho report"""

import csv
import ast
import os
import json
from ansible.module_utils.basic import AnsibleModule


class Results(object):
    """The class Results contains the functionality to parse
    data passed in from the playbook and to output it in the
    csv format in the file path specified.
    """

    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.file_path = module.params['file_path']
        self.vals = module.params['vals']

    def write_to_csv(self):
        """Output report data to file in csv format"""
        f_path = self.file_path
        with open(f_path, 'w') as write_file:
            file_size = os.path.getsize(f_path)
            vals = ast.literal_eval(self.vals)
            fields = vals[0].keys()
            fields.sort()
            writer = csv.writer(write_file, delimiter=',')
            if file_size == 0:
                writer.writerow(fields)
            for data in vals:
                sorted_keys = data.keys()
                sorted_keys.sort()
                sorted_values = []
                for k in sorted_keys:
                    sorted_values.append(data[k])
                writer.writerow(sorted_values)


def main():
    """Function to trigger collection of results and write
    them to csv file
    """
    module = AnsibleModule(argument_spec=dict(name=dict(required=True),
                                              file_path=dict(required=True),
                                              vals=dict(required=True)))
    results = Results(module=module)
    results.write_to_csv()
    vals = json.dumps(results.vals)
    module.exit_json(changed=False, meta=vals)


if __name__ == '__main__':
    main()
