"""Three commands for looking at /etc files on the remote machine."""

import sys
# for expat exceptions...
import xml

import gettext

from ansible.module_utils import rho_cmd  # pylint: disable=no-name-in-module

# for parsing systemid
if sys.version_info > (3,):
    import xmlrpc.client as xmlrpclib  # pylint: disable=import-error
else:
    import xmlrpclib  # pylint: disable=import-error

T = gettext.translation('rho', 'locale', fallback=True)
_ = T.ugettext


# pylint: disable=too-few-public-methods
class _GetFileRhoCmd(rho_cmd.RhoCmd):
    """This is a private superclass that does not
    directly wrap around particular command
    string(s) but is used as a stencil for
    classes that wrap around command strings
    related to getting information by reading
    files on the box.
    """

    def __init__(self):
        super(_GetFileRhoCmd, self).__init__()

        self.name = "file"

        self.filename = None

        self.cmd_string_template = "if [ -f %s ] ; then cat %s ; fi"

        self.cmd_names["get_file"] = ["%s.contents" % self.name]

    def parse_data(self):
        """Method that contains the functionality to
        parse results and populate the file name
        field depending on what file it's trying
        to access.
        """
        self.data["%s.contents" % self.name] = '"' + \
            "".join(self.cmd_results[self.cmd_names.keys()[0]][0]).\
            strip().replace('\n', '').replace('\r', '') + '"'


# pylint: disable=too-few-public-methods
class EtcIssueRhoCmd(_GetFileRhoCmd):
    """This class wraps around the command string
    to obtain information from the file '/etc/issue'.
    """

    def __init__(self):
        super(EtcIssueRhoCmd, self).__init__()

        self.name = "etc-issue"

        self.filename = "/etc/issue"

        cmd_string = self.cmd_string_template % (self.filename, self.filename)
        self.cmd_strings['get_file'] = cmd_string

        self.cmd_names["get_file"].append('etc-issue.etc-issue')

        self.fields = {'etc-issue.etc-issue': _('contents of /etc/issue')}

    def parse_data(self):
        """This method parses ad fills the information
        for the field 'etc-issue'.
        """
        super(EtcIssueRhoCmd, self).parse_data()
        self.data["etc-issue.etc-issue"] = '"' + \
                                           self.cmd_results[
                                               self.cmd_names.keys()[
                                                   0]][0].strip().\
                                           replace('\n', '').\
                                           replace('\r', '') \
                                           + '"'


# pylint: disable=too-few-public-methods
class InstnumRhoCmd(_GetFileRhoCmd):
    """This class wraps around the command string
    to obtain info from the file '/etc/sysconfig/rhn/install-num'
    """

    def __init__(self):
        super(InstnumRhoCmd, self).__init__()

        self.name = "instnum"

        self.filename = "/etc/sysconfig/rhn/install-num"

        cmd_string = self.cmd_string_template % (self.filename, self.filename)
        self.cmd_strings['get_file'] = cmd_string

        self.cmd_names["get_file"].append('instnum.instnum')

        self.fields = {'instnum.instnum': _('installation number')}

    def parse_data(self):
        super(InstnumRhoCmd, self).parse_data()
        self.data["instnum.instnum"] = str.strip(
            self.cmd_results[self.cmd_names.keys()[0]][0])


# pylint: disable=too-few-public-methods
class SystemIdRhoCmd(_GetFileRhoCmd):
    """This class wraps around the command string to
    obtain infro from the file '/etc/sysconfig/rhn/systemid'.
    """

    def __init__(self):
        super(SystemIdRhoCmd, self).__init__()
        self.name = "systemid"
        self.filename = "/etc/sysconfig/rhn/systemid"
        cmd_string = self.cmd_string_template % (self.filename, self.filename)
        self.cmd_strings['get_file'] = cmd_string
        # There are more fields here, not sure it's worth including
        # them as options
        self.cmd_names["get_file"].append('systemid.system_id')
        self.cmd_names["get_file"].append('systemid.username')
        self.fields = {'systemid.system_id': _('Red Hat Network system id'),
                       'systemid.username': _('Red Hat Network username')}

    def parse_data(self):
        """This method parses results and fills in
        information for the fields system_id and
        username.
        """
        super(SystemIdRhoCmd, self).parse_data()
        # if file is empty, or we get errors, skip...
        if not self.cmd_results[self.cmd_names.keys()[0]][0] \
                or self.cmd_results[self.cmd_names.keys()[0]][1]:
            # no file, nothing to parse
            return
        blob = "".join(self.cmd_results[self.cmd_names.keys()[0]])
        # loads returns param/methodname, we just want the params
        # and only the first param at that
        try:
            systemid = xmlrpclib.loads(blob)[0][0]
        except xml.parsers.expat.ExpatError:
            # log here? not sure it would help...
            return
        for key in systemid:
            self.data["%s.%s" % (self.name, key)] = systemid[key]
