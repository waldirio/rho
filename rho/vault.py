#
# Copyright (c) 2009-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

""" Vault is used to read and write data securely using the Ansible vault """

from __future__ import print_function
import os
import json
import uuid
from tempfile import gettempdir
from shutil import move
from getpass import getpass
from ansible.parsing.vault import VaultLib


def read_vault_password(vault_password_file):
    """ Reads vault password from file for scripting
    :param vault_password_file: Path to vault password file
    :returns: vault password string
    """
    vault_password = None
    if os.path.isfile(vault_password_file):
        with open(vault_password_file, 'r') as vault_file:
            lines = vault_file.readlines()
            for line in lines:
                vault_password = line.replace('\n', '')
                break

    return vault_password


def get_vault_password():
    """ Requests the users password from the command line """
    prompt = "Please enter your rho vault password: "
    return getpass("\033[01;36m" + prompt + "\033[0m")


def get_vault(vaultfile=None):
    """ Helper method that will get the vault password via input file or from
    standard input and then initialize a vault for users
    :param vaultfile: The location of a file with the vault password
    :returns: An initialized vault
    """
    vault_pass = None
    if vaultfile:
        vault_pass = read_vault_password(vaultfile)
    if vault_pass is None:
        vault_pass = get_vault_password()
    return Vault(vault_pass)


class Vault(object):
    """ R/W an ansible-vault file """

    def __init__(self, password):
        self.password = password
        self.vault = VaultLib(password)

    def load(self, stream):
        """ Read vault steam and return python object
        :param stream: The stream to read data from
        :returns: The decrypted data
        """
        return self.vault.decrypt(stream)

    def load_secure_file(self, secure_file):
        """ Read vault secured file and return python object
        :param secure_file: The file to read data from
        :returns: The decrpted data
        """
        return self.load(open(secure_file).read())

    def load_as_json(self, secure_file):
        """ Read vault secured file and return json decoded object
        :param secure_file: The file to read data from as json
        :returns: The JSON data
        """
        return json.loads(self.load_secure_file(secure_file))

    def dump(self, data, stream=None):
        """ Encrypt data and print stdout or write to stream
        :param data: The information to be encrypted
        :param stream: If not None the location to write the encrypted data to.
        :returns: If stream is None then the encrypted bytes otherwise None.
        """
        encrypted = self.vault.encrypt(data)
        if stream:
            stream.write(encrypted)
        else:
            return encrypted

    def dump_as_json(self, obj, stream=None):
        """ Convert object to json and encrypt the data.
        :param obj: Python object to convert to json
        :param stream: If not None the location to write the encrypted data to.
        :returns: If stream is None then the encrypted bytes otherwise None.
        """
        data = json.dumps(obj, separators=(',', ': '))
        return self.dump(data, stream)

    def dump_as_json_to_file(self, obj, file_path):
        """ Convert object to json and encrypt the data.
        :param obj: Python object to convert to json
        :param file_path: The file to write data to via temp file
        """
        tempdir = gettempdir()
        tempfilename = 'tmp_' + str(uuid.uuid4())
        temppath = os.path.join(tempdir, tempfilename)
        with open(temppath, 'wb') as data_temp:
            self.dump_as_json(obj, data_temp)
        data_temp.close()
        move(temppath, os.path.abspath(file_path))
