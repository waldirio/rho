-----------------------
Command Syntax & Usage
-----------------------
The basic syntax is:

``rho command subcommand [options]``

There are eight rho commands:
 * ``auth`` - for managing auth entries
 * ``profile`` - for managing profile entries
 * ``scan`` - for running scans
 * ``auth`` and ``profile`` both have three subcommands:
 * ``add`` - to create a new entry
 * ``edit`` - to modify an existing entry
 * ``clear`` - to remove any or all entries
 * ``show`` and ``list`` - to display one or more entries

The complete list of options for each command and subcommand are listed in the
rho manpage with other usage examples. The common options are listed with the
examples in this document.

^^^^^^^^^^^^^
Auth Entries
^^^^^^^^^^^^^
The first step to configuring rho is adding auth credentials to use to connect
over SSH. Each authentication identity requires its own auth entry.

``rho auth add --name server1creds --username rho-user --sshkeyfile /etc/ssh/ssh_host_rsa_key``

*Note:* --password not being passed or passed as empty are considered the same thing.

^^^^^^^^^
Profiles
^^^^^^^^^
Then, create the profile to use for the scan. This should include a list of IP
addresses or ranges, and the auth identity to use.

``rho profile edit --name profile1 --hosts "1.2.3.0 - 1.2.3.255" --auth server1creds server2creds``

The hosts can be passed in as a file with all the ranges listed in newlines.

^^^^^^^^^
Scanning
^^^^^^^^^
The arguments required for a scan are the profile to use, the file path for the report
and the facts to be collected. Optionally we can pass the number of Ansible forks.
Finally an important argument is ``reset``. This tells rho that the profile you are
passing in is either new or has been updated with changes in either the hosts or
auths or both and that rho has to process it afresh.

``rho scan --reset --profile profile1 --facts default --reportfile report.csv``

Since rho collects the successful host auth mappings from a full scan with reset
the user doesn't have to worry about iterating through multiple auths and hosts
again and again in the same profile as long as the profile hasn't changed.
For purposes of record keeping the host mapping files are always written to whenever
a scan is done using a profile. When profiles are deleted the host auth mappings
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

^^^^^^^
Output
^^^^^^^
The important part about a scan is the results report. By default,
this contains a large amount of information about the operating system, hardware, and platform.

- ``cpu.count`` - number of processors
- ``cpu.cpu_family`` - cpu family
- ``cpu.model_name`` - cpu model name
- ``cpu.vendor_id`` - cpu vendor name
- ``dmi.bios-vendor`` - bios vendor name
- ``error`` - any errors that are found
- ``etc-release.etc-release`` - contents of /etc/release (or equivalent)
- ``instnum.instnum`` installation number
- ``redhat-release.name`` - name of package that provides 'redhat-release'
- ``redhat-release.release`` - release of package that provides 'redhat-release'
- ``redhat-release.version`` - version of package that provides 'redhat-release'
- ``systemid.system_id`` - Red Hat Network System ID
- ``systemid.username`` - Red Hat Network username
- ``virt.virt`` - host, guest, or baremetal
- ``virt.type`` - type of virtual system
- ``uname.all`` - ``uname -a`` (all)
- ``uname.hardware_platform`` - ``uname -i`` (hardware_platform)
- ``uname.hostname`` - ``uname -n`` (hostname)
- ``uname.kernel`` - ``uname -r`` (kernel)
- ``uname.os`` - ``uname -s`` (os)
- ``uname.processor`` - ``uname -p`` (processor)

The output can then be configured to contain any combination of these fields by using the
``--facts`` argument. The following is the format rho understands for all the facts. Some or all
of these facts can be requested by either as a CLI list i.e. ``--facts <fact_1> <fact_2>`` etc
or by passing in a file with a new fact on every line in the format as follows. A value
of 'default' will get all the information listed above.

- **Username_uname.x** - for facts of the form ``uname.x``
- **VirtWhat_virt.x** - for facts of the form ``virt.x``
- **SysId_systemid.x** - for facts of the form ``systemid.x``
- **RedhatRelease_redhat-release.x** - for facts of the form ``redhat-release.x``
- **Instnum_instnum.x** - for facts of the form ``instnum.x``
- **EtcRelease_etc-release.x** - for facts of the form ``etc-release.x``
- **Dmi_dmi.x** - for facts of the form ``dmi.x``
- **Cpu_cpu.x** - for facts of the form ``cpu.x``

As hinted at previously, the auths that have been used in a particular scan are
the first valid auths in the list passed in order to the profile. All the valid
auths are of course listed in the host auth mapping file for the profile for that
scan identified by the timestamp.

For further details of the command usage view the following
`example <command_example.rst>`_.
