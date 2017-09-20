rho
===

Name
----

rho - Easily discover and manage product entitlement metadata in your network.


Synopsis
--------

``rho command subcommand [options]``

Description
-----------

rho is a network discovery tool to identify the number of systems running on a network, their operating system and versions of some key packages and products for almost any Linux or Unix flavor. Being able to identify the systems running on the network is a vital component to managing entitlements (licenses and renewals). Ultimately, discovery is part of the larger sysadmin task of managing inventories.

rho uses two configuration entries to manage the discovery process. *Profiles* define the network or subnet that is being monitored. *Credentials* contains the usernames, passwords or, alternatively, the SSH keys of the user which discovery runs as. There can be multiple network profiles and authentication credentials, used in any combination.

rho is an *agentless* discovery tool, so there is no need to install anything on multiple systems. Discovery for the entire network is centralized in a single machine.

This man page covers the commands, subcommands and options for rho with basic usage information. For more detailed information and examples, including best practices, see the rho README.

Usage
-----

rho performs three major tasks:

1. Creating authentication profiles. This has the basic command:

**rho auth add ...**

2. Creating network profiles. This has the basic command:

**rho profiles add --name=X --hosts X Y Z --auth A B**

3. Running discovery, such as:

**rho scan --profile=X --reportfile=Y**

The following sections cover these commands in more detail.

The primary purpose of rho is to scan a network. This can be done using simply ``rho scan`` using network and authentication profiles.

By default, the authentication credentials, profiles created using rho are stored in encrypted files. The files are encrypted with AES-256 encryption and is decrypted when the ``rho`` command is run, using a vault password to access the file.

Authentication
--------------

The first part to configuring rho is setting up authentication credentials. rho uses SSH to connect to the servers on the network, and the username and password or ssh key are used for authentication credentials. An authentication credential is passed when the scan is run by reference in a profile.

There can be multiple auth credentials contained in a single profile.

Creating and Editing Authentication Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

rho uses SSH credentials to access the servers to get their system information during discovery. These credentials can be either a username-password or username-key pair. Each set of credentials is stored in a separate entry.

**rho auth add --name=** *name* **--username=** *username* **[--password]** **[--sshkeyfile=** *key_file* **]** **[--sudo-password]** **[--vault=** *vault_file* **]**

``--name=name``

  This required argument sets the name of the new authentication credentials entry. This should be descriptive, such as identifying the user or server it relates to. For example, ``"server1-rhouser"``. It should never contain the actual password, as this name may be logged or printed during rho execution.


``--username=username``

  This required argument contains the username of the SSH identity will use to bind to the server.

``--password``

  The argument prompts for the password for the --username identity.

``--sshkeyfile=key_file``

  Optionally, this contains the path and filename of the file containing the SSH key issued for the --username identity.

``--sudo-password``

  The argument prompts for the password to be used with those commands that run on remote systems utilizing sudo.

``--vault=vault_file``

  This contains the path and filename of the file containing the vault password. If this option is used the file should be limited in access on the system.

The information given in an auth entry -- such as a password, sudo password, SSH keys, or even the username -- may change. For example, network security may require passwords to be updated every few months. The auth entry can be edited to change the SSH credential information. The parameters for ``rho auth edit`` are the same as those for ``rho auth add``.

**rho auth edit --name=** *name* **--username=** *username* **[--sshkeyfile=** *key_file* **]** **[--password]** **[--sudo-password]** **[--vault=** *vault_file* **]**

Listing and Showing Authentication Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``rho auth list`` command returns the details for every auth entry configured for rho. This output includes the name, username, password, ssh keyfile and sudo password for each entry. Passwords are masked if provided, if not they will appear as ‘null’.

**rho auth list [--vault=** *vault_file* **]**

``--vault=vault_file``

  This contains the path and filename of the file containing the vault password. If this option is used the file should be limited in access on the system.

The ``rho auth show`` command is the same as the ``rho auth list`` command, except that it only returns details for a single specified auth entry.

**rho auth show --name=** *name* **[--vault=** *vault_file* **]**

``--name=name``

  This required argument gives the authentication credentials entry to display.

``--vault=vault_file``

  This contains the path and filename of the file containing the vault password. If this option is used the file should be limited in access on the system.

Deleting Authentication Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It can be necessary to remove authentication credentials as the network infrastructure changes. This is done using the ``clear`` subcommand.

**IMPORTANT:** Remove the auth setting from any profile which uses it *before* removing the auth entry. Otherwise, any attempt to use the profile attempts to use the non-existent auth entry, which causes the ``rho`` command to fail.

**rho auth clear --name** *name* **| --all [--vault=** *vault_file* **]**

``--name=name``

  This argument gives the authentication credentials entry to delete.

``--all``

  This deletes all stored authentication credentials.

``--vault=vault_file``

  This contains the path and filename of the file containing the vault password. If this option is used the file should be limited in access on the system.

Profiles
--------

*Profiles* define a collection of network information, including IP addresses, SSH port, and SSH credentials. A discovery scan can reference a profile so that running the scan is automatic and repeatable, without having to re-enter network information every time.

Creating and Editing Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A profile is essentially a concise collection of the information that rho needs to connect to a network or system. This means it contains servers to connect to and authentication credentials to use. Each of these parameters allowed multiple entries, so the same profile can access a patchwork of servers and subnets, as needed.

**rho profile add --name=** *name* **--hosts** *ip_address* **--auth** *auth_profile* **[--sshport=** *ssh_port* **] [--vault=** *vault_file* **]**

``--name=name``

  This required argument sets the name of the new profile. This name is used to identify the profile in later operations. Use a descriptive name, such as ``"ColoSubnet"``.

``--hosts ip_address``

  This sets the IP address, hostname, or IP address range to use when running discovery. You may provide a list of hosts or a file where each item is on a separate line. There are several different formats that are allowed for the *ip_address* value.

  1. A specific hostname:

    --hosts server.example.com

  2. A specific IP address:

    --hosts 1.2.3.4

  3. An IP address range:

    --hosts "1.2.3.[4:255]"

``--auth auth_profile``

  This contains the name of the authentication profile (created with ``rho auth add``) to use to authentication to the servers being scanned. To add more than one auth profile to the network profile provide a list separated with a space. For example:

  ``--auth first_auth second_auth``

  IMPORTANT: This auth profile must exist before attempting to add the authentication profile to the network profile.

``--sshport=ssh_port``

  This value is used to support discovery on a non-standard port. Discovery takes place by default on port 22.

``--vault=vault_file``

  This contains the path and filename of the file containing the vault password. If this option is used the file should be limited in access on the system.

**rho profile edit --name** *name* **[--hosts** *ip_address* **] [--auth** *auth_profile* **] [--sshport=** *ssh_port* **] [--vault=** *vault_file* **]**

Although all three ``rho profile`` parameters accept more than one setting, the ``rho profile edit`` command is not additive. If a new argument is passed, it overwrites whatever was originally in the profile, it doesn't add a new attribute, even if the parameter is multi-valued. To add or keep multiple values with the edit command, list all parameters in the edit. For example, if a profile was created with an auth value of ``"server1creds"`` and the same profile will be used to scan with both server1creds and server2creds, edit as follows:

rho profile edit --name=myprofile --auth server1creds server2creds

You can use ``rho profile show --name=myprofile`` to make sure that the profile was properly edited.

Listing and Showing Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``list`` commands lists the details for all configured profiles. The output includes the IP ranges, auth credentials, and ports for the profile.

**rho profile list [--vault=** *vault_file* **]**

``--vault=vault_file``

  This contains the path and filename of the file containing the vault password. If this option is used the file should be limited in access on the system.

The ``rho profile show`` command is the same as the ``rho profile list`` command, except that it returns details for a single specific profile. This is a handy command to verify edits to a profile.

**rho profile show --name=** *profile* **[--vault=** *vault_file* **]**

``--name=profile``

  This argument gives the profile to display.

``--vault=vault_file``

  This contains the path and filename of the file containing the vault password. If this option is used the file should be limited in access on the system.

Deleting Profiles
~~~~~~~~~~~~~~~~~

Any or all profiles can be deleted using the ``clear`` subcommand.

**rho profile clear --name=** *name* **| --all [--vault=** *vault_file* **]**

``--name=name``

  This argument gives the profile to delete.

``--all``

  This deletes all stored profiles.

``--vault=vault_file``

  This contains the path and filename of the file containing the vault password. If this option is used the file should be limited in access on the system.

Facts
-----

The ``fact`` command is used to understand information that can be reported or to alter the contents of a report created from the ``rho scan`` command.

Listing Facts
~~~~~~~~~~~~~

A list of facts that can be gathered during the scanning process can be obtained with the ``list`` command.

**rho fact list [--filter=** *reg_ex* **]**

``--filter=reg_ex``

  Optionally, provide a filter view of the list of facts with a regular expression -- e.g ``uname.*``.

Hashing Facts
~~~~~~~~~~~~~

Sensitive facts can be encrypted within a report CSV file using the ``hash`` command. The facts that are hashed with this command are: *connection.host, connection.port, uname.all,* and *uname.hostname.*

**rho fact hash --reportfile=** *file* **[--outputfile=** *path* **]**

``--reportfile=file``

  The path and filename of the comma-separated values (CSV) file to read.

``--outputfile=path``

  The path and filename of the comma-separated values (CSV) file to be written.

Scanning
--------

The ``scan`` command is the one that actually runs discovery on the network. This command scans all of the servers within the range, and then writes the information to a CSV file.

A scan can be run by specifying the profile to use and where to write the CSV file:

**rho scan --profile=** *profile_name* **--reportfile=** *file* **[--facts** *file or list of facts* **] [--scan-dirs=** *file or list of remote directories* **] [--cache] [--vault=** *vault_file* **] [--logfile=** *log_file* **] [--ansible-forks=** *num_forks* **]**

``--profile=profile_name``

  Gives the name of the profile to use to run the scan.

``--reportfile=file``

  Writes the output to a comma-separated values (CSV) file.

``--facts fact1 fact2``

  The list of facts that are returned in the scan output. You may provide a list of facts or a file where each item is on a separate line. The list below is included as an example and is not exhaustive. Please use the ’rho fact list’ command to get the full list of available facts.

::

  cpu.count: number of processors
  cpu.cpu_family: cpu family
  cpu.model_name: cpu model name
  cpu.vendor_id: cpu vendor name
  dmi.bios-vendor: bios vendor name
  etc-release.etc-release: contents of /etc/release (or equivalent)
  instnum.instnum: installation number
  connection.uuid: unique id associate with scan
  connection.ip: ip address
  connection.port: ssh port
  redhat-release.name: name of package that provides 'redhat-release'
  redhat-release.release: release of package that provides 'redhat-release'
  redhat-release.version: version of package that provides 'redhat-release'
  systemid.system_id: Red Hat Network system id
  systemid.username: Red Hat Network username
  virt.virt: host, guest, or baremetal
  virt.type: type of virtual system
  uname.all: uname -a (all)
  uname.hardware_platform: uname -i (hardware_platform)
  uname.hostname: uname -n (hostname)
  uname.kernel: uname -r (kernel)
  uname.os: uname -s (os)
  uname.processor: uname -p (processor)
  
``--scan-dirs dir1 dir2``

  The list of directories on remote systems to scan for products. This option is intended to help scope a scan for systems with very large file system under the root directory. You may provide a list of directories or a file where each item is on a separate line.

``--cache``

  This argument can be used if a profile has previously been used for a discovery and nothing new needs to be found during the scan

``--vault=vault_file``

  This contains the path and filename of the file containing the vault password. If this option is used the file should be limited in access on the system.

``--logfile=log_file``

  This contains the path and filename of the file for writing the scan log.

``--ansible-forks=num_forks``

  This value is used to determine the number of systems to scan in parallel. The current default is 50 concurrent connections.

Options for All Commands
------------------------

A the following option is allowed with every command for rho.

``--help``

  This prints the help for the rho command or subcommand.

``-v``

  The verbose mode (``-vvv`` for more, ``-vvvv`` to enable connection debugging).

Examples
--------

:Adding new authentication credentials with a keyfile: ``rho auth add --name=new-creds --username=rho-user --sshkeyfile=/etc/ssh/ssh_host_rsa_key``
:Adding new authentication credentials with a password: ``rho auth add --name=other-creds --username=rho-user-pass --password``
:Creating a new profile: ``rho profile add --name=new-profile --hosts 1.2.3.0 --auth new-creds``
:Editing a profile: ``rho profile edit --name=new-profile --hosts 1.2.3.[0:255] --auth new-creds other-creds``
:Running a scan with a profile: ``rho scan --profile=new-profile --reportfile=/home/jsmith/Desktop/output.csv``

Security Considerations
-----------------------

The credentials used to access servers are stored with the profile configuration in an AES-256 encrypted configuration file. A vault password is used to access this file. The vault password and decrypted file contents are in the system memory, and could theoretically be written to disk if they were to be swapped out.

While the vault password can be passed via a file to run ``rho`` without prompts (such as scheduling a cron job), using this can be risky and should be stored in a location with limited access; be cautious about using this mechanism.

Authors
-------

The rho tool was originally written by Adrian Likins <alikins-at-redhat.com>, Devan Goodwin <dgoodwin-at-redhat.com>, Jesus M. Rodriguez <jesusr-at-redhat.com>, and Chris Snyder <csnyder@redhat.com> of Red Hat, Inc.
rho has been continued to be enhanced by Karthik Harihar Reddy Battula <karthikhhr@gmail.com>, Chris Hambridge <chambrid@redhat.com>, and Noah Lavine <nlavine@redhat.com>.

Copyright
---------

(c) 2017 Red Hat, Inc. Licensed under the GNU Public License version 2.
