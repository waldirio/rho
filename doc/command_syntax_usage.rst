-----------------------
Command Syntax & Usage
-----------------------
The basic syntax is:

``rho command subcommand [options]``

There are four rho commands:
 * ``auth`` - for managing auth entries
 * ``profile`` - for managing profile entries
 * ``scan`` - for running scans
 * ``fact`` - to show information about the facts rho can collect

``auth`` and ``profile`` both have five subcommands:
 * ``add`` - to create a new entry
 * ``edit`` - to modify an existing entry
 * ``clear`` - to remove any or all entries
 * ``show`` - to display a specific entry
 * ``list`` - to display one or more entries

``fact`` has three subcommands:
  * ``list`` - to display the list of facts that can be scanned
  * ``redact`` - to remove sensitive facts from a scanned report
  * ``encrypt`` - to encrypt sensitive facts within report

The complete list of options for each command and subcommand are listed in the
rho manpage with other usage examples. The common options are listed with the
examples in this document.

^^^^^^^^^^^^^
Auth Entries
^^^^^^^^^^^^^
The first step to configuring rho is adding auth credentials to use to connect
over SSH. Each authentication identity requires its own auth entry.

``rho auth add --name=server1creds --username=rho-user --sshkeyfile=/etc/ssh/ssh_host_rsa_key``

*Note:* --password not being passed or passed as empty are considered the same thing.

^^^^^^^^^
Profiles
^^^^^^^^^
Then, create the profile to use for the scan. This should include a list of IP
addresses or ranges, and the auth identity to use.

``rho profile add --name=profile1 --hosts 1.2.3.[0:255] --auth server1creds server2creds``

The hosts can be passed in as a file with all the ranges listed in newlines. Example below:

``rho profile edit --name=profile1 --hosts hosts_file --auth server1creds server2creds``

where ``hosts_file`` contains the ip address or ranges separated by newlines::

  1.2.3.1
  1.2.3.14
  1.2.4.34

^^^^^^^^^
Scanning
^^^^^^^^^
The options required for a scan are the profile to use and the file path for
the report. Optionally we can pass the number of Ansible forks and the facts to
be collected. Finally the ``cache`` option tells rho that the profile you are
providing has already been processed for connection mappings.

``rho scan --profile=profile1 --reportfile=report.csv``

Since rho collects the successful host auth mappings from a full scan
the user doesn't have to worry about iterating through multiple auths and hosts
again and again in the same profile as long as the profile hasn't changed when
utilizing the ``cache`` option. For purposes of record keeping the host
mapping files are always written to whenever a scan is done using a profile.
When profiles are deleted the host auth mappings
corresponding to the profile are renamed with prefix *(DELETED PROFILE)* so that
they are recognizable. Every scan has a timestamp in the mappings.

As far as the auths used by the inventory of a particular scan is concerned, it
is important to note that the order of the auths passed into a profile matters.
A profile by definition takes in one ordering of auths and all the hosts in
the profile are tested in that order with the auths before the first auths to
work are picked to run the fact collection. Therefore, it's up to the user
to pass in auths as per the priority they deem fit for a profile. If a non root
auth is better tried first and then the root auth then the user has to pass in the
auths in the order as ``--auth <nonroot_1> <nonroot_2> <root_1> <root_2>`` etc.

The output of the Ansible process is saved to `data/scan_log` by
default, for debugging. This location can be changed with the
`--logfile` flag.

^^^^^^^^^^^^
Common Flags
^^^^^^^^^^^^

All rho commands accept the `-v` flag, which increases the verbosity
of rho's output. It comes in four varieties: `-v`, `-vv`, `-vvv`, and
`-vvvv`, with more `v`'s indicating more verbose output. The verbose
output can be useful in debugging.

^^^^^^^
Output
^^^^^^^
The important part about a scan is the results report. By default,
this contains a large amount of information about the operating system, hardware, and platform.


- ``connection.host`` - The host address of the connection
- ``connection.port`` - The port used for the connection
- ``connection.uuid`` - A generated identifier for the connection
- ``cpu.bogomips`` - measurement of CPU speed made by the Linux kernel
- ``cpu.count`` - number of processors
- ``cpu.cpu_family`` - cpu family
- ``cpu.model_name`` - cpu model name
- ``cpu.model_ver`` - cpu model version
- ``cpu.socket_count`` - number of sockets
- ``cpu.vendor_id`` - cpu vendor name
- ``date.anaconda_log`` - /root/anaconda-ks.cfg modified time
- ``date.date`` - date
- ``date.filesystem_create`` - uses tune2fs -l on the / filesystem dev found using mount
- ``date.machine_id`` - /etc/machine-id modified time'
- ``date.yum_history`` - dates from yum history
- ``dmi.bios-vendor`` - bios vendor name
- ``dmi.bios-version`` - bios version info
- ``dmi.processor-family`` - processor family
- ``dmi.system-manufacturer`` - system manufacturer
- ``etc-issue.etc-issue`` - contents of /etc/issue (or equivalent)
- ``etc-release.name`` - name of the release
- ``etc-release.release`` - release information
- ``etc-release.version`` - release version
- ``instnum.instnum`` - installation number
- ``jboss.brms.drools_core_ver`` - Drools version
- ``jboss.brms.kie_api_ver`` - KIE API version
- ``jboss.brms.kie_war_ver`` - KIE runtime version
- ``jboss.deploy_dates`` - List of deployment dates of JBoss installations
- ``jboss.fuse.activemq-ver`` - ActiveMQ version
- ``jboss.fuse.camel-ver`` - Camel version
- ``jboss.fuse.cxf-ver`` - CXF version
- ``jboss.installed_versions`` - List of installed versions of JBoss
- ``jboss.running_versions`` - List of running versions of JBoss
- ``redhat-packages.is_redhat`` - determines if package is a Red Hat package
- ``redhat-packages.last_installed`` - last installed package
- ``redhat-packages.last_built`` - last built package
- ``redhat-packages.num_rh_packages`` - number of Red Hat packages
- ``redhat-packages.num_installed_packages`` - number of installed packages
- ``redhat-release.name`` - name of package that provides 'redhat-release'
- ``redhat-release.release`` - release of package that provides 'redhat-release'
- ``redhat-release.version`` - version of package that provides 'redhat-release'
- ``subman.cpu.core(s)_per_socket`` - cpu cores per socket from subscription manager
- ``subman.cpu.cpu(s)`` - cpus from subscription manager
- ``subman.cpu.cpu_socket(s)`` - cpu sockets from subscription manager
- ``subman.virt.is_guest`` - Whether is a virtual guest from subscription manager
- ``subman.virt.host_type`` - Virtual host type from subscription manager
- ``subman.virt.uuid`` - Virtual host uuid from subscription manager
- ``systemid.system_id`` - Red Hat Network System ID
- ``systemid.username`` - Red Hat Network username
- ``uname.all`` - ``uname -a`` (all)
- ``uname.hardware_platform`` - ``uname -i`` (hardware_platform)
- ``uname.hostname`` - ``uname -n`` (hostname)
- ``uname.kernel`` - ``uname -r`` (kernel)
- ``uname.os`` - ``uname -s`` (os)
- ``uname.processor`` - ``uname -p`` (processor)
- ``virt.num_guests`` - the number of virtualized guests
- ``virt.num_running_guests`` - the number of running virtualized guests
- ``virt.type`` - type of virtual system
- ``virt.virt`` - host, guest, or baremetal
- ``virt-what.type`` - What type of virtualization a system is running

The output can then be configured to contain any combination of these fields by using the
``--facts`` option. The following is the format rho understands for all the facts. Some or all
of these facts can be requested by either as a CLI list i.e. ``--facts <fact_1> <fact_2>`` etc
or by passing in a file with a new fact on every line in the format as follows. A value
of 'default' will get all the information listed above.

For further details of the command usage view the following
`example <command_example.rst>`_.

^^^^^^^^^^^^^^^^^^^^^
Scan User Permissions
^^^^^^^^^^^^^^^^^^^^^
Some of the output facts will report an error if the user used to perform the
scan does not have the appropriate permissions to execute the command used to
gather the targeted facts. The following set of facts require *admin/root*
permissions to collect the facts:

- ``dmi.x``
- ``subman.x``
- ``virt-what.x``

The scan user can successful collect these values if the user is **root** or
has the ability to perform a ``sudo``. The following
provides the necessary content for the ``/etc/sudoers`` file where *scanuser*
represents the username used for the scan.

::

  Cmnd_Alias SCAN = /sbin/subscription-manager, /usr/sbin/dmidecode, /usr/sbin/virt-what
  scanuser ALL=NOPASSWD: SCAN

If the scan user uses a password to sudo, one can be given with the
`--sudo-password` option to the `auth add` and `auth edit`
commands. The sudo-with-password fundtionality can be tested by using
the 'askpass' box in the Vagrantfile.
