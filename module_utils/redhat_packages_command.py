# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Look for Red Hat packages on the remote machine."""

import sys

from ansible.module_utils import rho_cmd  # pylint: disable=no-name-in-module

if sys.version_info > (3,):
    long = int  # pylint: disable=invalid-name,redefined-builtin


# pylint: disable=too-few-public-methods

class RedhatPackagesRhoCmd(rho_cmd.RhoCmd):
    """This class wraps around the cli commands
    that are used to obtain information about
    Redhat packages installed on the box. Currently
    there are 5 fields associated with this class.
    There is only one command string that has to be
    run for all the 5 fields.
    """

    def __init__(self):
        super(RedhatPackagesRhoCmd, self).__init__()

        self.name = "packages"

        self.cmd_strings['get_package_info'] = 'rpm -qa --qf ' \
                                               '"%{NAME}|%{VERSION}' \
                                               '|%{RELEASE}'' \
                                               ''|%{INSTALLTIME}' \
                                               '|%{VENDOR}' \
                                               '|%{BUILDTIME}' \
                                               '|%{BUILDHOST}'' \
                                               ''|%{SOURCERPM}' \
                                               '|%{LICENSE}' \
                                               '|%{PACKAGER}'' \
                                               ''|%{INSTALLTIME:date}' \
                                               '|%{BUILDTIME:date}\n"'

        self.cmd_names['get_package_info'] = ['redhat-packages.is_redhat',
                                              'redhat-'
                                              'packages.num_rh_packages',
                                              'redhat-'
                                              'packages.num_'
                                              'installed_packages',
                                              'redhat-'
                                              'packages.last_installed',
                                              'redhat-'
                                              'packages.last_built']

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

    def parse_data(self):
        """Main method to parse data and to handle errors if
        the command string returns invalid results.
        """
        if self.cmd_results['get_package_info'][1]:
            self.data['redhat-packages.is_redhat'] = "error"
            self.data['redhat-packages.num_rh_packages'] = "error"
            self.data['redhat-packages.num_installed_packages'] = "error"
            self.data['redhat-packages.last_installed'] = "error"
            self.data['redhat-packages.last_built'] = "error"
            return
        installed_packages = [self.PkgInfo(self, line, "|")
                              for line in
                              self.cmd_results['get_package_info'][0]
                              .splitlines()]
        rh_packages = filter(self.PkgInfo.is_red_hat_pkg,
                             installed_packages)
        if len(rh_packages) > 0:  # pylint: disable=len-as-condition
            last_installed = 0
            last_built = 0
            max_install_time = float("-inf")
            max_build_time = float("-inf")
            for pkg in rh_packages:
                if pkg.install_time > max_install_time:
                    max_install_time = pkg.install_time
                    last_installed = pkg
                if pkg.build_time > max_build_time:
                    max_build_time = pkg.build_time
                    last_built = pkg

            # pylint: disable=len-as-condition
            is_red_hat = "Y" if len(rh_packages) > 0 else "N"

            self.data['redhat-packages.is_redhat'] = is_red_hat
            self.data['redhat-packages.num_rh_packages'] = len(rh_packages)
            self.data['redhat-packages.num_installed_packages'] \
                = len(installed_packages)
            self.data['redhat-packages.last_installed'] \
                = last_installed.details_install()
            self.data['redhat-packages.last_built'] \
                = last_built.details_built()
        else:
            last_installed = ""
            last_built = ""
            is_red_hat = ""

            self.data['redhat-packages.is_redhat'] = is_red_hat
            self.data['redhat-packages.num_rh_packages'] = len(rh_packages)
            self.data['redhat-packages.num_installed_packages'] \
                = len(installed_packages)
            self.data['redhat-packages.last_installed'] = last_installed
            self.data['redhat-packages.last_built'] = last_built
