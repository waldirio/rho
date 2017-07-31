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

    # pylint: disable=too-many-instance-attributes
    class PkgInfo(object):
        """This is an inner class for RedhatPackagesRhoCmd
        class and provides functionality to parse the
        results of running the (only) command string
        named 'get_package_info'. This is purely to
        make the parsing cleaner and understandable.
        """

        def __init__(self, outer, row, separator):
            self.outer = outer
            cols = row.split(separator)
            if len(cols) < 10:
                raise outer.PkgInfoParseException()
            else:
                self.name = cols[0]
                self.version = cols[1]
                self.release = cols[2]
                self.install_time = long(cols[3])
                self.vendor = cols[4]
                self.build_time = long(cols[5])
                self.build_host = cols[6]
                self.source_rpm = cols[7]
                self.license = cols[8]
                self.packager = cols[9]
                self.install_date = cols[10]
                self.build_date = cols[11]
                self.is_red_hat = False
                if ('redhat.com' in self.build_host and
                        'fedora' not in self.build_host and
                        'rhndev' not in self.build_host):
                    self.is_red_hat = True

                # Helper methods to help with recording data in
                # requested fields.

        def is_red_hat_pkg(self):
            """Determines if package is a Red Hat package.
            :returns: True if Red Hat, False otherwise
            """
            return self.is_red_hat

        def details_built(self):
            """Provides information on when the package was built
            :returns: String including details and build date
            """
            return "%s Built: %s" % (self.details(), self.build_date)

        def details_install(self):
            """Provides information on when the package was installed.
            :returns: String including installation date
            """
            return "%s Installed: %s" % (self.details(), self.install_date)

        def details(self):
            """Provides package details including name, version and release.
            :returns: String including name, version and release
            """
            return "%s-%s-%s" % (self.name, self.version, self.release)

    class PkgInfoParseException(BaseException):
        """Defining an exception for failing to parse package information
        """
        pass

    def handle_systemid(self, data):
        """Process the output of systemid.contents
        and supply the appropriate output information
        """
        if 'systemid.contents' in data:
            blob = data['systemid.contents']
            id_in_facts = 'SysId_systemid.system_id' in self.fact_names
            username_in_facts = 'SysId_systemid.username' in self.fact_names
            try:
                systemid = xmlrpclib.loads(blob)[0][0]
                if id_in_facts and 'system_id'in systemid:
                    data['systemid.system_id'] = systemid['system_id']
                if username_in_facts and 'usnername' in systemid:
                    data['systemid.username'] = systemid['usnername']
            except xml.parsers.expat.ExpatError:
                if id_in_facts:
                    data['systemid.system_id'] = 'error'
                if username_in_facts:
                    data['systemid.username'] = 'error'

            del data['systemid.contents']
        return data

    # pylint: disable=too-many-locals, too-many-branches
    def handle_redhat_packages(self, data):
        """ Process the output of redhat-packages.results
        and supply the appropriate output information
        """
        if 'redhat-packages.results' in data:
            installed_packages = [self.PkgInfo(self, line, "|")
                                  for line in
                                  data['redhat-packages.results']]
            rh_packages = filter(self.PkgInfo.is_red_hat_pkg,
                                 installed_packages)

            rhpkg_prefix = 'RedhatPackages_redhat-packages.'
            is_rhpkg_str = rhpkg_prefix + 'is_redhat'
            num_rh_str = rhpkg_prefix + 'num_rh_packages'
            installed_pkg_str = rhpkg_prefix + 'num_installed_packages'
            last_installed_str = rhpkg_prefix + 'last_installed'
            last_built_str = rhpkg_prefix + 'last_built'
            is_rhpkg_in_facts = is_rhpkg_str in self.fact_names
            num_rh_in_facts = num_rh_str in self.fact_names
            installed_pkg_in_facts = installed_pkg_str in self.fact_names
            last_installed_in_facts = last_installed_str in self.fact_names
            last_built_in_facts = last_built_str in self.fact_names

            if rh_packages:
                last_installed = None
                last_built = None
                max_install_time = float("-inf")
                max_build_time = float("-inf")
                for pkg in rh_packages:
                    if pkg.install_time > max_install_time:
                        max_install_time = pkg.install_time
                        last_installed = pkg
                    if pkg.build_time > max_build_time:
                        max_build_time = pkg.build_time
                        last_built = pkg

                is_red_hat = "Y" if rh_packages > 0 else "N"

                if is_rhpkg_in_facts:
                    data['redhat-packages.is_redhat'] = is_red_hat
                if num_rh_in_facts:
                    data['redhat-packages.num_rh_packages'] = len(rh_packages)
                if installed_pkg_in_facts:
                    data['redhat-packages.num_installed_packages'] = (
                        len(installed_packages))
                if last_installed_in_facts:
                    data['redhat-packages.last_installed'] = (
                        last_installed.details_install()
                        if last_installed else 'none')
                if last_built_in_facts:
                    data['redhat-packages.last_built'] = (
                        last_built.details_built() if last_built else 'none')
            else:
                if num_rh_in_facts:
                    data['redhat-packages.num_rh_packages'] = len(rh_packages)
                if installed_pkg_in_facts:
                    data['redhat-packages.num_installed_packages'] \
                        = len(installed_packages)
            del data['redhat-packages.results']
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
                fields.remove('redhat-packages.results')
            except ValueError:
                pass
            writer = csv.writer(write_file, delimiter=',')
            if file_size == 0:
                writer.writerow(fields)
            for data in vals:
                data = self.handle_systemid(data)
                data = self.handle_redhat_packages(data)
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
