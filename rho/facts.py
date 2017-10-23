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

    if fact_names == []:
        facts_to_collect.update(DEFAULT_FACTS)

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

    facts_to_collect.update(ALWAYS_COLLECT)

    bad_facts = facts_to_collect.difference(ALL_FACTS)
    if bad_facts:
        log.error('Unknown facts requested: %s', ', '.join(sorted(bad_facts)))
        sys.exit(1)

    return facts_to_collect


# pylint: disable=too-many-arguments
def new_fact(fact_name, description, is_sensitive=False,
             is_default=True, always_collect=False,
             categories=None):
    """Define a new fact.

    :param fact_name: the name of the fact.
    :param description: a short description of the fact, for 'rho fact list'
        and the documentation.
    :param is_sensitive: whether this fact should be redacted by
        'rho fact hash'.
    :param is_default: whether this fact should be scanned for by default.
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


new_fact('connection.host', 'The host address of the connection',
         is_sensitive=True, always_collect=True)
new_fact('connection.port', 'The port used for the connection',
         is_sensitive=True, always_collect=True)
new_fact('connection.uuid', 'A generated identifier for the connection',
         always_collect=True)
new_fact('cpu.bogomips', 'measurement of CPU speed made by the Linux kernel',
         categories=[RHEL_FACTS])
new_fact('cpu.count', 'number of processors',
         categories=[RHEL_FACTS])
new_fact('cpu.core_count', 'number of cores',
         categories=[RHEL_FACTS])
new_fact('cpu.cpu_family', 'cpu family',
         categories=[RHEL_FACTS])
new_fact('cpu.hyperthreading', 'Whether cpu is hyperthreaded',
         categories=[RHEL_FACTS])
new_fact('cpu.model_name', 'cpu model name',
         categories=[RHEL_FACTS])
new_fact('cpu.model_ver', 'cpu model version',
         categories=[RHEL_FACTS])
new_fact('cpu.socket_count', 'number of sockets',
         categories=[RHEL_FACTS])
new_fact('cpu.vendor_id', 'cpu vendor name',
         categories=[RHEL_FACTS])
new_fact('date.anaconda_log', '/root/anaconda-ks.cfg modified time',
         categories=[RHEL_FACTS])
new_fact('date.date', 'date',
         categories=[RHEL_FACTS])
new_fact('date.filesystem_create',
         'uses tune2fs -l on the / filesystem dev found using mount',
         categories=[RHEL_FACTS])
new_fact('date.machine_id', "/etc/machine-id modified time'",
         categories=[RHEL_FACTS])
new_fact('date.yum_history', 'dates from yum history',
         categories=[RHEL_FACTS])
new_fact('dmi.bios-vendor', 'bios vendor name',
         categories=[RHEL_FACTS])
new_fact('dmi.bios-version', 'bios version info',
         categories=[RHEL_FACTS])
new_fact('dmi.processor-family', 'processor family',
         categories=[RHEL_FACTS])
new_fact('dmi.system-manufacturer', 'system manufacturer',
         categories=[RHEL_FACTS])
new_fact('etc-issue.etc-issue', 'contents of /etc/issue (or equivalent)',
         categories=[RHEL_FACTS])
new_fact('etc_release.name', 'name of the release',
         categories=[RHEL_FACTS])
new_fact('etc_release.release', 'release information',
         categories=[RHEL_FACTS])
new_fact('etc_release.version', 'release version',
         categories=[RHEL_FACTS])
new_fact('instnum.instnum', 'installation number',
         categories=[RHEL_FACTS])
new_fact('jboss.brms.drools-core-ver', 'Drools version')
new_fact('jboss.brms.kie-api-ver', 'KIE API version')
new_fact('jboss.brms.kie-war-ver', 'KIE runtime version')
new_fact('jboss.eap.common-directories',
         'Presence of common directories for JBoss EAP',
         categories=[JBOSS_FACTS])
new_fact('jboss.eap.deploy-dates',
         'List of deployment dates of JBoss EAP installations')
new_fact('jboss.eap.installed-versions',
         'List of installed versions of JBoss EAP')
new_fact('jboss.eap.jboss-user', "Whether a user called 'jboss' exists",
         categories=[JBOSS_FACTS])
new_fact('jboss.eap.packages', 'Installed RPMs that look like JBoss',
         categories=[JBOSS_FACTS])
new_fact('jboss.eap.processes', 'Running processes that look like JBoss',
         categories=[JBOSS_FACTS])
new_fact('jboss.eap.running-versions', 'List of running versions of JBoss EAP',
         categories=[JBOSS_FACTS])
new_fact('jboss.fuse.activemq-ver', 'ActiveMQ version')
new_fact('jboss.fuse.camel-ver', 'Camel version')
new_fact('jboss.fuse.cxf-ver', 'CXF version')
new_fact('redhat-packages.is_redhat',
         'determines if package is a Red Hat package',
         categories=[RHEL_FACTS])
new_fact('redhat-packages.last_installed', 'last installed package',
         categories=[RHEL_FACTS])
new_fact('redhat-packages.last_built', 'last built package',
         categories=[RHEL_FACTS])
new_fact('redhat-packages.num_rh_packages', 'number of Red Hat packages',
         categories=[RHEL_FACTS])
new_fact('redhat-packages.num_installed_packages',
         'number of installed packages',
         categories=[RHEL_FACTS])
new_fact('redhat-release.name',
         "name of package that provides 'redhat-release'",
         categories=[RHEL_FACTS])
new_fact('redhat-release.release',
         "release of package that provides 'redhat-release'",
         categories=[RHEL_FACTS])
new_fact('redhat-release.version',
         "version of package that provides 'redhat-release'",
         categories=[RHEL_FACTS])
new_fact('subman.cpu.core(s)_per_socket',
         'cpu cores per socket from subscription manager',
         categories=[RHEL_FACTS])
new_fact('subman.cpu.cpu(s)', 'cpus from subscription manager',
         categories=[RHEL_FACTS])
new_fact('subman.cpu.cpu_socket(s)', 'cpu sockets from subscription manager',
         categories=[RHEL_FACTS])
new_fact('subman.has_facts_file',
         'Whether subscription manager has a facts file',
         categories=[RHEL_FACTS])
new_fact('subman.virt.is_guest',
         'Whether is a virtual guest from subscription manager',
         categories=[RHEL_FACTS])
new_fact('subman.virt.host_type',
         'Virtual host type from subscription manager',
         categories=[RHEL_FACTS])
new_fact('subman.virt.uuid', 'Virtual host uuid from subscription manager',
         categories=[RHEL_FACTS])
new_fact('systemid.system_id', 'Red Hat Network System ID',
         categories=[RHEL_FACTS])
new_fact('systemid.username', 'Red Hat Network username',
         categories=[RHEL_FACTS])
new_fact('uname.all', 'uname -a (all)',
         is_sensitive=True,
         categories=[RHEL_FACTS])
new_fact('uname.hardware_platform', 'uname -i (hardware_platform)',
         categories=[RHEL_FACTS])
new_fact('uname.hostname', 'uname -n (hostname)',
         is_sensitive=True,
         categories=[RHEL_FACTS])
new_fact('uname.kernel', 'uname -r (kernel)',
         categories=[RHEL_FACTS])
new_fact('uname.os', 'uname -s (os)',
         categories=[RHEL_FACTS])
new_fact('uname.processor', 'uname -p (processor)',
         categories=[RHEL_FACTS])
new_fact('virt.num_guests', 'the number of virtualized guests',
         categories=[RHEL_FACTS])
new_fact('virt.num_running_guests', 'the number of running virtualized guests',
         categories=[RHEL_FACTS])
new_fact('virt.type', 'type of virtual system',
         categories=[RHEL_FACTS])
new_fact('virt.virt', 'host, guest, or baremetal',
         categories=[RHEL_FACTS])
new_fact('virt-what.type', 'What type of virtualization a system is running',
         categories=[RHEL_FACTS])
