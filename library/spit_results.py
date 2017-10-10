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
    long = int  # pylint: disable=invalid-name,redefined-builtin
else:
    import xmlrpclib  # pylint: disable=import-error

EAP_CLASSIFICATIONS = {
    'JBoss_4_0_0': 'JBossAS-4',
    'JBoss_4_0_1_SP1': 'JBossAS-4',
    'JBoss_4_0_2': 'JBossAS-4',
    'JBoss_4_0_3_SP1': 'JBossAS-4',
    'JBoss_4_0_4_GA': 'JBossAS-4',
    'Branch_4_0': 'JBossAS-4',
    'JBoss_4_2_0_GA': 'JBossAS-4',
    'JBoss_4_2_1_GA': 'JBossAS-4',
    'JBoss_4_2_2_GA': 'JBossAS-4',
    'JBoss_4_2_3_GA': 'JBossAS-4',
    'JBoss_5_0_0_GA': 'JBossAS-5',
    'JBoss_5_0_1_GA': 'JBossAS-5',
    'JBoss_5_1_0_GA': 'JBossAS-5',
    'JBoss_6.0.0.Final': 'JBossAS-6',
    'JBoss_6.1.0.Final': 'JBossAS-6',
    '1.0.1.GA': 'JBossAS-7',
    '1.0.2.GA': 'JBossAS-7',
    '1.1.1.GA': 'JBossAS-7',
    '1.2.0.CR1': 'JBossAS-7',
    '1.2.0.Final': 'WildFly-8',
    '1.2.2.Final': 'WildFly-8',
    '1.2.4.Final': 'WildFly-8',
    '1.3.0.Beta3': 'WildFly-8',
    '1.3.0.Final': 'WildFly-8',
    '1.3.3.Final': 'WildFly-8',
    '1.3.4.Final': 'WildFly-9',
    '1.4.2.Final': 'WildFly-9',
    '1.4.3.Final': 'WildFly-9',
    '1.4.4.Final': 'WildFly-10',
    '1.5.0.Final': 'WildFly-10',
    '1.5.1.Final': 'WildFly-10',
    '1.5.2.Final': 'WildFly-10',
    'JBPAPP_4_2_0_GA': 'EAP-4.2',
    'JBPAPP_4_2_0_GA_C': 'EAP-4.2',
    'JBPAPP_4_3_0_GA': 'EAP-4.3',
    'JBPAPP_4_3_0_GA_C': 'EAP-4.3',
    'JBPAPP_5_0_0_GA': 'EAP-5.0.0',
    'JBPAPP_5_0_1': 'EAP-5.0.1',
    'JBPAPP_5_1_0': 'EAP-5.1.0',
    'JBPAPP_5_1_1': 'EAP-5.1.1',
    'JBPAPP_5_1_2': 'EAP-5.1.2',
    'JBPAPP_5_2_0': 'EAP-5.2.0',
    '1.1.2.GA-redhat-1': 'EAP-6.0.0',
    '1.1.3.GA-redhat-1': 'EAP-6.0.1',
    '1.2.0.Final-redhat-1': 'EAP-6.1.0',
    '1.2.2.Final-redhat-1': 'EAP-6.1.1',
    '1.3.0.Final-redhat-2': 'EAP-6.2',
    '1.3.3.Final-redhat-1': 'EAP-6.3',
    '1.3.4.Final-redhat-1': 'EAP-6.3',
    '1.3.5.Final-redhat-1': 'EAP-6.3',
    '1.3.6.Final-redhat-1': 'EAP-6.4',
    '1.3.7.Final-redhat-1': 'EAP-6.4',
    '1.4.4.Final-redhat-1': 'EAP-7.0',
    '1.5.1.Final-redhat-1': 'EAP-7.0',
    '1.5.4.Final-redhat-1': 'EAP-7.0'
}

BRMS_CLASSIFICATIONS = {
    '6.4.0.Final-redhat-3': 'BRMS 6.3.0',
    '6.3.0.Final-redhat-5': 'BRMS 6.2.0',
    '6.2.0.Final-redhat-4': 'BRMS 6.1.0',
    '6.0.3-redhat-6': 'BRMS 6.0.3',
    '6.0.3-redhat-4': 'BRMS 6.0.2',
    '6.0.2-redhat-6': 'BRMS 6.0.1',
    '6.0.2-redhat-2': 'BRMS 6.0.0',
    '5.3.1.BRMS': 'BRMS 5.3.1',
    '5.3.0.BRMS': 'BRMS 5.3.0',
    '5.2.0.BRMS': 'BRMS 5.2.0',
    '5.1.0.BRMS': 'BRMS 5.1.0',
    '5.0.2.BRMS': 'BRMS 5.0.2',
    '5.0.1.BRMS': 'BRMS 5.0.1',
    'drools-core-5.0.0': 'BRMS 5.0.0',
    '6.5.0.Final': 'Drools 6.5.0'
}

FUSE_CLASSIFICATIONS = {
    'redhat-630187': 'Fuse-6.3.0',
    'redhat-621084': 'Fuse-6.2.1',
    'redhat-620133': 'Fuse-6.2.0',
    'redhat-611412': 'Fuse-6.1.1',
    'redhat-610379': 'Fuse-6.1.0',
    'redhat-60024': 'Fuse-6.0.0',
}


def iteritems(dictionary):
    """Iterate over a dictionary's (key, value) pairs using Python 2 or 3.

    :param dictionary: the dictionary to iterate over.
    """

    if sys.version_info[0] == 2:
        return dictionary.iteritems()

    return dictionary.items()


def safe_next(iterator):
    """Get the next item from an iterator, in Python 2 or 3.

    :param iterator: the iterator.
    """

    if sys.version_info[0] == 2:
        return iterator.next()

    return next(iterator)


def safe_ansible_property(ansible_vars, fact_name, prop):
    """Get a property of the JSON output of an Ansible raw task.

    Handles missing and skipped tasks safely.

    Usage:
      output = safe_ansible_property(ansible_vars,
                                     'jboss.eap.jar-ver',
                                     'stdout')
      if output:
        further_processing(output)

    :param ansible_vars: the raw vars dictionary from Ansible.
    :param fact_name: the fact to retrieve.
    :param prop: the property to return.
    :returns: the property, or None if not available.
    """

    if fact_name not in ansible_vars:
        return None

    output = ansible_vars[fact_name]
    if 'skipped' in output and output['skipped'] is True:
        return None

    return output[prop]


JBOSS_EAP_INSTALLED_VERSIONS = 'jboss.eap.installed-versions'
JBOSS_EAP_DEPLOY_DATES = 'jboss.eap.deploy-dates'
JBOSS_EAP_RUNNING_VERSIONS = 'jboss.eap.running-versions'


# JBoss versions are processed separately from other *-ver data
# because they merge data from two input facts and include deploy
# dates as well as version strings.
def process_jboss_versions(fact_names, host_vars):
    """Get JBoss version information from the host_vars.

    :param fact_names: the set of fact names the user requested.
    :param host_vars: the host vars from Ansible.
    :returns: a dict of key-value pairs to output.
    """

    lines = []
    val = {}

    # host_vars is not used after this function (data that we return
    # is copied to host_vals instead), so by not adding
    # jboss.eap.jar_ver and jboss.eap.run_jar_ver to val, we are
    # implicitly removing them from the output.
    lines.extend(safe_ansible_property(host_vars,
                                       'jboss.eap.jar-ver',
                                       'stdout_lines') or [])
    lines.extend(safe_ansible_property(host_vars,
                                       'jboss.eap.run-jar-ver',
                                       'stdout_lines') or [])

    jboss_releases = []
    deploy_dates = []
    for line in lines:
        if line:
            line_format = line.split('**')
            version = line_format[0]
            deploy_date = line_format[-1]
            deploy_dates.append(deploy_date)
            if version in EAP_CLASSIFICATIONS:
                jboss_releases.append(EAP_CLASSIFICATIONS[version])
            elif version.strip():
                jboss_releases.append('Unknown-Release: ' + version)

    def empty_output_message(val, name):
        """Give the right error message for missing data.

        For data that depends on having Java.

        :param val: a value. Considered missing if falsey.
        :param name: the thing we were searching for.
        :returns: the val if true, otherwise a useful error message.
        """

        if val:
            return val
        if not host_vars['have_java']:
            return 'N/A (java not found)'
        return '({0} not found)'.format(name)

    if JBOSS_EAP_INSTALLED_VERSIONS in fact_names:
        val[JBOSS_EAP_INSTALLED_VERSIONS] = (
            empty_output_message('; '.join(jboss_releases), 'jboss'))
    if JBOSS_EAP_DEPLOY_DATES in fact_names:
        val[JBOSS_EAP_DEPLOY_DATES] = (
            empty_output_message('; '.join(deploy_dates), 'jboss'))
    if JBOSS_EAP_RUNNING_VERSIONS in fact_names:
        val[JBOSS_EAP_RUNNING_VERSIONS] = (
            empty_output_message(
                safe_ansible_property(host_vars,
                                      JBOSS_EAP_RUNNING_VERSIONS,
                                      'stdout'),
                'running jboss'))

    return val


def classify_releases(lines, classifications):
    """Classify release strings using a dictionary."""

    releases = []
    for line in lines:
        if line:
            if line in classifications:
                releases.append(classifications[line])
            else:
                releases.append('Unknown-Release: ' + line)

    return '; '.join(releases)


def process_addon_versions(fact_names, host_vars):
    """Classify release strings for JBoss BRMS and FUSE.

    :param fact_names: the set of fact names that the user requested.
    :param host_vars: the host vars from Ansible.
    :returns: a dict of key-value pairs to output.
    """

    result = {}

    def classify(key, fact_names, classifications):
        """Classify a particular key."""

        if key in fact_names:
            lines = safe_ansible_property(host_vars, key, 'stdout_lines') or []
            classes = classify_releases(lines, classifications)
            if classes:
                result[key] = classes
            else:
                result[key] = '({0} not found)'.format(key)

    classify('jboss.brms.kie-api-ver', fact_names, BRMS_CLASSIFICATIONS)
    classify('jboss.brms.drools-core-ver', fact_names, BRMS_CLASSIFICATIONS)
    classify('jboss.brms.kie-war-ver', fact_names, BRMS_CLASSIFICATIONS)

    classify('jboss.fuse.activemq-ver', fact_names, FUSE_CLASSIFICATIONS)
    classify('jboss.fuse.camel-ver', fact_names, FUSE_CLASSIFICATIONS)
    classify('jboss.fuse.cxf-ver', fact_names, FUSE_CLASSIFICATIONS)

    return result


def remove_newlines(data):
    """ Processes input data values and strips out any newlines
    """
    for key in data:
        if isinstance(data[key], str):
            data[key] = data[key].replace('\r\n', '')
    return data


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
        self.all_vars = module.params['all_vars']
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
            rh_packages = list(filter(self.PkgInfo.is_red_hat_pkg,
                                      installed_packages))

            rhpkg_prefix = 'redhat-packages.'
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

                is_red_hat = "Y" if rh_packages else "N"

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
        # Make sure the controller expanded the default option.
        assert self.fact_names != ['default']

        keys = set(self.fact_names)

        # Special processing for JBoss facts.
        for _, host_vars in iteritems(self.all_vars):
            uuid = host_vars['connection']['connection.uuid']
            host_vals = safe_next((vals
                                   for vals in self.vals
                                   if vals['connection.uuid'] == uuid))

            host_vals.update(process_jboss_versions(keys, host_vars))
            host_vals.update(process_addon_versions(keys, host_vars))

        # Process System ID.
        for data in self.vals:
            data = self.handle_systemid(data)
            data = self.handle_redhat_packages(data)
            data = remove_newlines(data)

        normalized_path = os.path.normpath(self.file_path)
        with open(normalized_path, 'w') as write_file:
            # Construct the CSV writer
            writer = csv.DictWriter(
                write_file, sorted(keys), delimiter=',')

            # Write a CSV header if necessary
            file_size = os.path.getsize(normalized_path)
            if file_size == 0:
                # handle Python 2.6 not having writeheader method
                if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
                    headers = {}
                    for fields in writer.fieldnames:
                        headers[fields] = fields
                    writer.writerow(headers)
                else:
                    writer.writeheader()

            # Write the data
            for data in self.vals:
                writer.writerow(data)


def main():
    """Function to trigger collection of results and write
    them to csv file
    """

    fields = {
        "name": {"required": True, "type": "str"},
        "file_path": {"required": True, "type": "str"},
        "vals": {"required": True, "type": "list"},
        "all_vars": {"required": True, "type": "dict"},
        "fact_names": {"required": True, "type": "list"}
    }

    module = AnsibleModule(argument_spec=fields)

    results = Results(module=module)
    results.write_to_csv()
    vals = json.dumps(results.vals)
    module.exit_json(changed=False, meta=vals)


if __name__ == '__main__':
    main()
