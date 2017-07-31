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
import os
import json
import sys
import xml
# pylint: disable=import-error
from ansible.module_utils.basic import AnsibleModule

# for parsing systemid
if sys.version_info > (3,):
    import xmlrpc.client as xmlrpclib  # pylint: disable=import-error
else:
    import xmlrpclib  # pylint: disable=import-error


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
        self.fact_names = module.params['fact_names']

    def handle_systemid(self, data):
        """Process the output of systemid.contents
        and supply the appropriate output information
        """
        if 'systemid.contents' in data:
            blob = data['systemid.contents']
            try:
                systemid = xmlrpclib.loads(blob)[0][0]
            except xml.parsers.expat.ExpatError:
                pass

            if 'SysId_systemid.system_id' in self.fact_names and ('system_id'
                                                                  in systemid):
                data['systemid.system_id'] = systemid['system_id']
            if 'SysId_systemid.username' in self.fact_names and ('usnername'
                                                                 in systemid):
                data['systemid.username'] = systemid['usnername']

            del data['systemid.contents']
        return data

    def write_to_csv(self):
        """Output report data to file in csv format"""
        f_path = os.path.normpath(self.file_path)
        with open(f_path, 'w') as write_file:
            file_size = os.path.getsize(f_path)
            vals = self.vals
            fields = sorted(vals[0].keys())
            try:
                fields.remove('systemid.contents')
            except ValueError:
                pass
            writer = csv.writer(write_file, delimiter=',')
            if file_size == 0:
                writer.writerow(fields)
            for data in vals:
                data = self.handle_systemid(data)
                sorted_keys = sorted(data.keys())
                sorted_values = []
                for k in sorted_keys:
                    # remove newlines and carriage returns
                    # from strings for proper csv printing
                    if isinstance(data[k], str):
                        sorted_values.append(data[k].replace('\n', ' ')
                                             .replace('\r', ''))
                    else:
                        sorted_values.append(data[k])
                writer.writerow(sorted_values)


def main():
    """Function to trigger collection of results and write
    them to csv file
    """

    fields = {
        "name": {"required": True, "type": "str"},
        "file_path": {"required": True, "type": "str"},
        "vals": {"required": True, "type": "list"},
        "fact_names": {"required": True, "type": "list"}
    }

    module = AnsibleModule(argument_spec=fields)

    results = Results(module=module)
    results.write_to_csv()
    vals = json.dumps(results.vals)
    module.exit_json(changed=False, meta=vals)


if __name__ == '__main__':
    main()
