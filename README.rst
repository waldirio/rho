.. image:: https://travis-ci.org/quipucords/rho.svg?branch=master
    :target: https://travis-ci.org/quipucords/rho
.. image:: https://coveralls.io/repos/github/quipucords/rho/badge.svg
    :target: https://coveralls.io/github/quipucords/rho


====================================================================
   rho - Tool for discovering RHEL, Linux, and Unix Servers
====================================================================

rho is a tool for scanning a network, logging into systems using SSH, and
retrieving information about available Unix and Linux servers.

This README contains information about installing rho, basic usage, known
issues, and best practices. For more details information about the available
command and command options with rho, see the *manpage*.

- `Intro to rho`_
- `Requirements & Assumptions`_
- `Installation`_
- `Command Syntax & Usage`_
- `Development`_
- `Issues`_
- `Changes`_
- `Authors`_
- `Contributing`_
- `Copyright & License`_

-------------
Intro to rho
-------------
rho is an Ansible-based network inventory tool. rho scans a user-defined range
of machines and then reports basic information about the operating system and
hardware for each server. rho simplifies some basic sysadmin tasks, like
managing licensing renewals and new deployments.

rho only has to be installed on a single central server to scan all of the
servers on a network or subnet. rho is an agent-less discovery tool built on
`Ansible <https://www.ansible.com/>`_, so there is no need to install
anything on any server but the one which will run the scans. Ansible uses SSH,
which is commonly available for server, on both the scanning server and the
target machines.

The rho tool itself is set up through two configuration items:
 * **auth entries**, which contain the username and password or SSH key to access
   each server
 * **profile entries**, which contain IP address ranges, and the auth credentials to use.

There can be multiple auth entries in each profile. A profile contains
all the hosts and ranges that are to be tested against the auths.

The rho tool configuration is created using rho itself. There are subcommands
to create and edit auth and profile items in the configuration. For example:

``rho auth add --name server1auth --username rho-user --sshkeyfile
/etc/ssh/ssh_host_rsa_key --password``

This creates a new auth item named server1auth, which uses the SSH user
rho-user with a key stored in the key file. The password is input as
a CLI prompt.

(The different rho commands are covered more in the `Command Syntax & Usage`_
section.)

All the information that rho needs is stored in the data folder in
the installed directory. All the auths are stored in the ``credentials``
file. All the profiles are stored in the ``profiles`` file. The Ansible
playbook is called ``rho_playbook.yml`` stored in the installed directory.
The roles created during the scan are stored in the ``roles`` folder. These
roles are used by ``rho_playbook.yml`` to perform the fact collection.

Running the scan is simple. Just point the rho tool to the profile
to use, the facts to collect and print the results to a CSV output file.
Optional parameters are the number of processes Ansible should use and whether
or not to process the profile using ``--cache``. A newly created or
freshly edited profile cannot be processed using cache as the program must
create an Ansible inventory called ``<profile name>_hosts.yml`` that includes the
working hosts matched with an auth each (the auths are chosen in the order
passed in to the profile add or edit command as will be explained later).

``rho scan --profile big_test --facts data/facts_eg --ansible_forks 100 --reportfile rep.csv``

The output is simple CSV format. If 'default' is the argument for ``--facts``,
the csv output contains the following information:

``OS,kernel,processor,platform,release name,release version,release number,system ID,username,instnum,release,CPU count,CPU vendor,CPU model,BIOS vendor,virtual guest/host,virtual type``

For example:

``Linux,i686,i386,redhat-release,5Client,5.3.0.3,ID-1000015943,
jsmith,da3122afdb7edd23,Red Hat Enterprise Linux Client release 5.3
(Tikanga),2,GenuineIntel,Intel(R) Core(TM)2 Duo CPU,Award Software, Inc.,host,
xen``

As implied by the report output, rho differentiates between baremetal machines,
virtual hosts, and virtual guests, and identifies several major virtual types
(Xen, Qemu, KVM, and VMWare). It can be very important for inventorying machines
and maintaining software licenses to separate virtual hosts from guests; rho
returns that information with every scan, by default.

--------------------------
Requirements & Assumptions
--------------------------
Before installing rho, there are some guidelines about which machine it should be installed on:
 * rho is written to run on RHEL or Fedora servers.
 * The machine that rho is installed on must be able to access the machines to be scanned, so it must be on the network and the machines must be running.
 * The target machines must be running SSH.
 * The user account that rho uses to SSH into the machine must have adequate permissions to run commands and read certain files.
 * The user account rho uses for a machine should have a sh like shell.  For example, it *cannot* be a /sbin/nologin or /bin/false shell.

These python packages are required for the rho install machine to run rho:
 * python
 * gettext
 * json
 * subprocess
 * xmlrpclib
 * ansible.module_utils.basic

The following python packages are required to build & test rho from source:
 * python-devel
 * python-setuptools
 * pytest
 * pytest-cov
 * Mock
 * flake8
 * pylint
 * Coverage

-------------
Installation
-------------
rho is available for `download <https://copr.fedorainfracloud.org/coprs/chambridge/rho/>`_ from fedora COPR.

1. First, make sure that the EPEL repo is enabled for the server.
You can find the appropriate architecture and version on the `EPEL wiki <https://fedoraproject.org/wiki/EPEL>`_::

  rpm -Uvh http://fedora-epel.mirrors.tds.net/fedora-epel/7/x86_64/e/epel-release-7-10.noarch.rpm

2. Next, add the COPR repo to your server.
You can find the appropriate architecture and version on the `COPR rho page <https://copr.fedorainfracloud.org/coprs/chambridge/rho/>`_::

  cd /etc/yum.repos.d/
  wget https://copr.fedorainfracloud.org/coprs/chambridge/rho/repo/epel-7/chambridge-rho-epel-7.repo

3. Then, install the rho package:

``yum install rho``

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

For expanded information on auth entries, profiles, scanning, and output read
the `syntax and usage document <doc/command_syntax_usage.rst>`_.

-----------------------
Development
-----------------------
Begin by cloning the repository::

    git clone git@github.com:quipucords/rho.git

rho currently supports Python 2.7, 3.5, 3.6. If you don't have Python on your
system follow these `instructions <https://www.python.org/downloads/>`_. Based
on your system you may be using either `pip` or `pip3` to install modules, for
simplicity the instructions below will specify `pip`.

^^^^^^^^^^^^^^^^^^^^^^^^
Installing Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^
From within the local clone root directory run the following command to install
dependencies needed for development and testing purposes::

    pip install -r requirements.txt

^^^^^^
Build
^^^^^^
In order to build rho run the following command::

    make build

^^^^^^^
Linting
^^^^^^^
In order to lint changes made to the source code execute the following command::

    make lint

^^^^^^^^^^^^^^^^^^^^^^^^
Testing
^^^^^^^^^^^^^^^^^^^^^^^^

Unit Testing
""""""""""""""

To run the unit tests with the interpreter available as ``python``, use::

    make tests

Continuous testing runs on travis:
`https://travis-ci.org/quipucords/rho <https://travis-ci.org/quipucords/rho>`_


Functional Testing
"""""""""""""""""""

To run end-to-end functional tests against local virtual machines follow the
information in `functional test document <doc/functional_test.rst>`_.


-------------
Issues
-------------
To report bugs for rho `open issues <https://github.com/quipucords/rho/issues>`_
against this repository in Github. Please complete the issue template when
opening a new bug to improve investigation and resolution time.

----------------
Changes
----------------
Track & find changes to the tool in `CHANGES <CHANGES.rst>`_.

--------
Authors
--------
Authorship and current maintainer information can be found in `AUTHORS <AUTHORS.rst>`_.

----------------
Contributing
----------------
Reference the `CONTRIBUTING <CONTRIBUTING.rst>`_ guide for information to the project.

--------------------
Copyright & License
--------------------
Copyright 2009-2017, Red Hat, Inc.

rho is released under the `GNU Public License version 2 <LICENSE>`_.
