# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

# At one point we had a bug where we added a new fact but forgot to
# add it to ALL_FACTS, so users couldn't select it. The way we define
# facts below is intended to make it impossible for that to happen
# again.

"""Defining the set of facts that Rho can scan for."""

import collections
import sys
from rho.utilities import log

ALWAYS_COLLECT = set()
SENSITIVE_FACTS = set()
DEFAULT_FACTS = set()
ALL_FACTS = set()

RHEL_FACTS = set()
JBOSS_FACTS = set()

# 'rho fact list' will print fact documentation in whatever order this
# dictionary's iterator returns them, so need to keep it sorted.
FACT_DOCS = collections.OrderedDict()


def expand_facts(fact_names):
    """Expand a list of facts with implicit facts and short names.

    :param fact_names: a list of fact names
    :returns: a set of facts to collect
    """

    facts_to_collect = set()

    for fact in fact_names:
        if fact == 'all':
            return ALL_FACTS

        if fact == 'default':
            facts_to_collect.update(DEFAULT_FACTS)
        elif fact == 'rhel':
            facts_to_collect.update(RHEL_FACTS)
        elif fact == 'jboss':
            facts_to_collect.update(JBOSS_FACTS)
        else:
            facts_to_collect.add(fact)

    if fact_names == []:
        facts_to_collect.update(DEFAULT_FACTS)

    facts_to_collect.update(ALWAYS_COLLECT)

    bad_facts = facts_to_collect.difference(ALL_FACTS)
    if bad_facts:
        log.error('Unknown facts requested: %s', ', '.join(sorted(bad_facts)))
        sys.exit(1)

    return facts_to_collect


# pylint: disable=too-many-arguments
def new_fact(fact_name, description, is_default,
             is_sensitive=False, always_collect=False,
             categories=None):
    """Define a new fact.

    :param fact_name: the name of the fact.
    :param description: a short description of the fact, for 'rho fact list'
        and the documentation.
    :param is_default: whether this fact should be scanned for by default.
    :param is_sensitive: whether this fact should be redacted by
        'rho fact hash'.
    :param always_collect: whether rho should always collect this fact.
    """

    ALL_FACTS.add(fact_name)
    if is_sensitive:
        SENSITIVE_FACTS.add(fact_name)
    if is_default:
        DEFAULT_FACTS.add(fact_name)
    if always_collect:
        ALWAYS_COLLECT.add(fact_name)

    FACT_DOCS[fact_name] = description

    # There's no point in categorizing a fact that we always collect.
    if always_collect:
        assert not categories

    if categories:
        for category in categories:
            category.add(fact_name)


new_fact('connection.host', 'The host address of the connection', True,
         is_sensitive=True, always_collect=True)
new_fact('connection.port', 'The port used for the connection', True,
         is_sensitive=True, always_collect=True)
new_fact('connection.uuid', 'A generated identifier for the connection', True,
         always_collect=True)
new_fact('cpu.bogomips', 'measurement of CPU speed made by the Linux kernel',
         True, categories=[RHEL_FACTS])
new_fact('cpu.count', 'number of processors', True,
         categories=[RHEL_FACTS])
new_fact('cpu.core_count', 'number of cores', True,
         categories=[RHEL_FACTS])
new_fact('cpu.cpu_family', 'cpu family', True,
         categories=[RHEL_FACTS])
new_fact('cpu.hyperthreading', 'Whether cpu is hyperthreaded', True,
         categories=[RHEL_FACTS])
new_fact('cpu.model_name', 'cpu model name', True,
         categories=[RHEL_FACTS])
new_fact('cpu.model_ver', 'cpu model version', True,
         categories=[RHEL_FACTS])
new_fact('cpu.socket_count', 'number of sockets', True,
         categories=[RHEL_FACTS])
new_fact('cpu.vendor_id', 'cpu vendor name', True,
         categories=[RHEL_FACTS])
new_fact('date.anaconda_log', '/root/anaconda-ks.cfg modified time', True,
         categories=[RHEL_FACTS])
new_fact('date.date', 'date', True,
         categories=[RHEL_FACTS])
new_fact('date.filesystem_create',
         'uses tune2fs -l on the / filesystem dev found using mount', True,
         categories=[RHEL_FACTS])
new_fact('date.machine_id', "/etc/machine-id modified time'", True,
         categories=[RHEL_FACTS])
new_fact('date.yum_history', 'dates from yum history', True,
         categories=[RHEL_FACTS])
new_fact('dmi.bios-vendor', 'bios vendor name', True,
         categories=[RHEL_FACTS])
new_fact('dmi.bios-version', 'bios version info', True,
         categories=[RHEL_FACTS])
new_fact('dmi.processor-family', 'processor family', True,
         categories=[RHEL_FACTS])
new_fact('dmi.system-manufacturer', 'system manufacturer', True,
         categories=[RHEL_FACTS])
new_fact('etc-issue.etc-issue', 'contents of /etc/issue (or equivalent)', True,
         categories=[RHEL_FACTS])
new_fact('etc_release.name', 'name of the release', True,
         categories=[RHEL_FACTS])
new_fact('etc_release.release', 'release information', True,
         categories=[RHEL_FACTS])
new_fact('etc_release.version', 'release version', True,
         categories=[RHEL_FACTS])
new_fact('instnum.instnum', 'installation number', True,
         categories=[RHEL_FACTS])
new_fact('jboss.brms.drools-core-ver', 'Drools version', False)
new_fact('jboss.brms.kie-api-ver', 'KIE API version', False)
new_fact('jboss.brms.kie-war-ver', 'KIE runtime version', False)
new_fact('jboss.eap.common-directories',
         'Presence of common directories for JBoss EAP', True,
         categories=[JBOSS_FACTS])
new_fact('jboss.eap.deploy-dates',
         'List of deployment dates of JBoss EAP installations', False)
new_fact('jboss.eap.installed-versions',
         'List of installed versions of JBoss EAP', False)
new_fact('jboss.eap.jboss-user', "Whether a user called 'jboss' exists", True,
         categories=[JBOSS_FACTS])
new_fact('jboss.eap.packages', 'Installed RPMs that look like JBoss', True,
         categories=[JBOSS_FACTS])
new_fact('jboss.eap.processes', 'Running processes that look like JBoss', True,
         categories=[JBOSS_FACTS])
new_fact('jboss.eap.running-versions', 'List of running versions of JBoss EAP',
         True, categories=[JBOSS_FACTS])
new_fact('jboss.fuse.activemq-ver', 'ActiveMQ version', False)
new_fact('jboss.fuse.camel-ver', 'Camel version', False)
new_fact('jboss.fuse.cxf-ver', 'CXF version', False)
new_fact('redhat-packages.certs', 'the list of Red Hat certificates found',
         True, categories=[RHEL_FACTS])
new_fact('redhat-packages.is_redhat',
         'determines if package is a Red Hat package', True,
         categories=[RHEL_FACTS])
new_fact('redhat-packages.last_installed', 'last installed package', True,
         categories=[RHEL_FACTS])
new_fact('redhat-packages.last_built', 'last built package', True,
         categories=[RHEL_FACTS])
new_fact('redhat-packages.num_rh_packages', 'number of Red Hat packages',
         True, categories=[RHEL_FACTS])
new_fact('redhat-packages.num_installed_packages',
         'number of installed packages', True,
         categories=[RHEL_FACTS])
new_fact('redhat-release.name',
         "name of package that provides 'redhat-release'", True,
         categories=[RHEL_FACTS])
new_fact('redhat-release.release',
         "release of package that provides 'redhat-release'", True,
         categories=[RHEL_FACTS])
new_fact('redhat-release.version',
         "version of package that provides 'redhat-release'", True,
         categories=[RHEL_FACTS])
new_fact('subman.consumed',
         True, 'consumed SKUs from subscription manager',
         categories=[RHEL_FACTS])
new_fact('subman.cpu.core(s)_per_socket',
         'cpu cores per socket from subscription manager', True,
         categories=[RHEL_FACTS])
new_fact('subman.cpu.cpu(s)', 'cpus from subscription manager', True,
         categories=[RHEL_FACTS])
new_fact('subman.cpu.cpu_socket(s)', 'cpu sockets from subscription manager',
         True, categories=[RHEL_FACTS])
new_fact('subman.has_facts_file',
         'Whether subscription manager has a facts file', True,
         categories=[RHEL_FACTS])
new_fact('subman.virt.is_guest',
         'Whether is a virtual guest from subscription manager', True,
         categories=[RHEL_FACTS])
new_fact('subman.virt.host_type',
         'Virtual host type from subscription manager', True,
         categories=[RHEL_FACTS])
new_fact('subman.virt.uuid', 'Virtual host uuid from subscription manager',
         True, categories=[RHEL_FACTS])
new_fact('systemid.system_id', 'Red Hat Network System ID', True,
         categories=[RHEL_FACTS])
new_fact('systemid.username', 'Red Hat Network username', True,
         categories=[RHEL_FACTS])
new_fact('uname.all', 'uname -a (all)', True,
         is_sensitive=True,
         categories=[RHEL_FACTS])
new_fact('uname.hardware_platform', 'uname -i (hardware_platform)', True,
         categories=[RHEL_FACTS])
new_fact('uname.hostname', 'uname -n (hostname)', True,
         is_sensitive=True,
         categories=[RHEL_FACTS])
new_fact('uname.kernel', 'uname -r (kernel)', True,
         categories=[RHEL_FACTS])
new_fact('uname.os', 'uname -s (os)', True,
         categories=[RHEL_FACTS])
new_fact('uname.processor', 'uname -p (processor)', True,
         categories=[RHEL_FACTS])
new_fact('virt.num_guests', 'the number of virtualized guests', True,
         categories=[RHEL_FACTS])
new_fact('virt.num_running_guests', 'the number of running virtualized guests',
         True, categories=[RHEL_FACTS])
new_fact('virt.type', 'type of virtual system', True,
         categories=[RHEL_FACTS])
new_fact('virt.virt', 'host, guest, or baremetal', True,
         categories=[RHEL_FACTS])
new_fact('virt-what.type', 'What type of virtualization a system is running',
         True, categories=[RHEL_FACTS])
