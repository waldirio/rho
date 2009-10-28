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

# this is based on "sshpt"  http://code.google.com/p/sshpt/

import gettext
t = gettext.translation('rho', 'locale', fallback=True)
_ = t.ugettext


from rho.log import log 

from optparse import OptionParser
import os
import re
import StringIO
import sys
import threading
import traceback
import Queue
import socket

import paramiko

import config


class BaseThread(threading.Thread):
    """ Parent class for all threads. """

    def quit(self):
        self.quitting = True


class OutputThread(BaseThread):
    """
    Prevent SSHThreads from simultaneously writing to the same file, 
    'kill -9' from destroying results, and allows you to do a tail -f on the
    report file to watch results in real time.
    """
    def __init__(self, output_queue, verbose=True, report=None):
        threading.Thread.__init__(self, name="OutputThread")
        self.output_queue = output_queue
        self.verbose = verbose
        self.quitting = False
        self.report = report
    
    def quit(self):
        self.quitting = True

    def write(self, queueObj):
        print queueObj.ip
        for rho_cmd in queueObj.rho_cmds:
            print rho_cmd.name, rho_cmd.data

    def run(self):
        while not self.quitting:
            queueObj = self.output_queue.get()
            if queueObj == "quit":
                self.quit()

            try:
                self.report.add(queueObj)
            except Exception, detail:
                log.error("Exception: %s" % detail)
                log.error(sys.exc_type())
                log.error(traceback.print_tb(sys.exc_info()[2]))
#                self.output_queue.task_done()
                self.quit()
#            self.write(queueObj)
            # somewhere in here, we return the data to...?
            self.output_queue.task_done()


class SSHThread(BaseThread):
    """
    Connect to a host and run commands.

    Must be instanciated with:

    Adds the following to the output queue before put():
        queueObj['host']
        queueObj['username']
        queueObj['password']
        queueObj['commands'] - List: Commands that were executed
        queueObj['connection_result'] - String: 'SUCCESS'/'FAILED'
        queueObj['command_output'] - String: Textual output of commands 
                                     after execution
    """
    def __init__ (self, id, ssh_connect_queue, output_queue):
        """
        Constructor

            id                    A thread ID
            ssh_connect_queue     Queue.Queue() for receiving orders
            output_queue          Queue.Queue() to output results
        """
        threading.Thread.__init__(self, name="SSHThread-%d" % (id,))
        self.ssh_connect_queue = ssh_connect_queue
        self.output_queue = output_queue
        self.id = id
        self.quitting = False

    def quit(self):
        self.quitting = True

    def run (self):
        try:
            while not self.quitting:
                queueObj = self.ssh_connect_queue.get()
                if queueObj == 'quit':
                    self.quit()
                    
#                success, command_output = attemptConnection(host, username, password, timeout, commands)
                attemptConnection(queueObj)

                #hmm, this is weird...
                if queueObj.connection_result:
                    queueObj.connection_result = "SUCCESS"
                else:
                    queueObj.connection_result = "FAILED"

                self.output_queue.put(queueObj)
                self.ssh_connect_queue.task_done()
                # just for progress, etc...
                if queueObj.output_callback:
                    queueObj.output_callback()
        except Exception, detail:
            log.error("Exception: %s" % detail)
            log.error(sys.exc_type())
            log.error(traceback.print_tb(sys.exc_info()[2]))
#            self.output_queue.task_done()
#            self.ssh_connect_queue.task_done()
            self.quit()

def startOutputThread(verbose, report):
    """ Starts up the OutputThread. """
    output_queue = Queue.Queue()
    output_thread = OutputThread(output_queue, verbose,report)
    output_thread.setDaemon(True)
    output_thread.start()
    return output_queue

def stopOutputThread():
    """ Shuts down the OutputThread. """
    for t in threading.enumerate():
        if t.getName().startswith('OutputThread'):
            t.quit()
    return True

def startSSHQueue(output_queue, max_threads):
    """
    Setup concurrent threads for testing SSH connectivity.  
    
    Must be passed a Queue (output_queue) for writing results.
    """
    ssh_connect_queue = Queue.Queue()
    for thread_num in range(max_threads):
        ssh_thread = SSHThread(thread_num, ssh_connect_queue, output_queue)
        ssh_thread.setDaemon(True)
        ssh_thread.start()
    return ssh_connect_queue

def stopSSHQueue():
    """ Shut down the SSHThreads. """
    for t in threading.enumerate():
        if t.getName().startswith('SSHThread'):
            t.quit()
    return True

def queueSSHConnection(ssh_connect_queue, cmd):
    """ Add files to the SSH Queue. (ssh_connect_queue) """
    ssh_connect_queue.put(cmd)
    return True

def get_pkey(auth):

    if auth.type != config.SSH_KEY_TYPE:
        return None

    fo = StringIO.StringIO(auth.key)
    # this is lame, but there doesn't appear to be any API to just
    # DWIM with the the key_data, I have to figure out if its RSA or DSA/DSS myself
    if fo.readline().find("-----BEGIN DSA PRIVATE KEY-----") > -1:
        fo.seek(0)
        pkey = paramiko.DSSKey.from_private_key(fo, password=auth.password)
        return pkey
    fo.seek(0)
    if fo.readline().find("-----BEGIN RSA PRIVATE KEY-----") > -1:
        fo.seek(0)
        pkey = paramiko.RSAKey.from_private_key(fo, password=auth.password)
        return pkey

    print _("The private key file for %s is not a recognized ssh key type" % auth.name)
    return None

def paramikoConnect(ssh_job):
    """
    Connects to 'host' and returns a Paramiko transport object to use 
    in further communications
    """

    # Copy the list of ports, we'll modify it as we go:
    ports_to_try = list(ssh_job.ports)

    found_port = None # we'll set this once we identify a port that works
    found_auth = False

    while True:
        if found_auth:
            break

        if found_port != None:
            log.warn("Found ssh on %s:%s, but no auths worked." %
                    (ssh_job.ip, found_port))
            break

        if len(ports_to_try) == 0:
            log.debug("Could not find/connect to ssh on: %s" % ssh_job.ip)
            err = _("unable to connect")
            ssh_job.error = err
            break

        port = ports_to_try.pop(0)

        for auth in ssh_job.auths:
            
            ssh_job.error = None

            debug_str = "%s:%s/%s" % (ssh_job.ip, port, auth.name)
            # this checks the case of a passphrase we can't decrypt
            try:
                pkey = get_pkey(auth)
            except paramiko.SSHException, detail:
                # paramiko throws an SSHException for pretty much everything... ;-<
                log.error("ssh key error for %s: %s" % (debug_str, str(detail)))
                ssh = str(detail)
                continue

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            try:
                log.info("trying: %s" % debug_str)

                ssh.connect(ssh_job.ip, port=int(port), 
                            username=auth.username,
                            password=auth.password,
                            pkey=pkey,
                            # FIXME: 
                            # we should probably set this somewhere
                            allow_agent=ssh_job.allow_agent,
                            look_for_keys=ssh_job.look_for_keys,
                            timeout=ssh_job.timeout)
                ssh_job.port = port
                ssh_job.auth = auth
                found_port = port
                found_auth = True
                log.info("success: %s" % debug_str)
                break

            # Implies we've found an SSH server listening:
            except paramiko.AuthenticationException, e:
                # Because we stop checking ports once we find one where ssh
                # is listening, we can report the error message here and it
                # will end up in the final report correctly:
                err = _("login failed")
                log.error(err)
                ssh_job.error = err
                ssh = str(e)
                found_port = port
                continue

            # No route to host:
            except socket.error, e:
                log.warn("No route to host, skipping port: %s" % debug_str)
                ssh = str(e)
                break

            # TODO: Hitting a live port that isn't ssh will result in
            # paramiko.SSHException, do we need to handle this explicitly?

            # Something else happened:
            except Exception, detail:
                log.warn("Connection error: %s - %s" % (debug_str,
                    str(detail)))
                ssh = str(detail)
                continue


    return ssh

def executeCommands(transport, rho_commands):
    host = transport.get_host_keys().keys()[0]
    for rho_cmd in rho_commands:
        output = []
        for cmd_string in rho_cmd.cmd_strings:
            stdin, stdout, stderr = transport.exec_command(cmd_string)
            # one item in the list for each cmd stdout
            output.append((stdout.read(), stderr.read()))
        rho_cmd.populate_data(output)
    return rho_commands

def attemptConnection(ssh_job):
    # ssh_job is a SshJob object

    if ssh_job.ip != "":
        try:
            ssh = paramikoConnect(ssh_job)
            if type(ssh) == type(""): # If ssh is a string that means the connection failed and 'ssh' is the details as to why
                ssh_job.command_output = ssh
                ssh_job.connection_result = False
                return
            command_output = []
            executeCommands(transport=ssh, rho_commands=ssh_job.rho_cmds)
            ssh.close()

        except Exception, detail:
            # Connection failed
            log.error("Exception on %s: %s" % (ssh_job.ip, detail))
            log.error(sys.exc_type())
            log.error(sys.exc_info())
            log.error(traceback.print_tb(sys.exc_info()[2]))
            ssh_job.connection_result = False
            ssh_job.command_output = detail
#            ssh.close()
