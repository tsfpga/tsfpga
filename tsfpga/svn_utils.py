# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import re
import subprocess


def get_svn_revision_information(cwd=None):
    check_that_svn_commands_are_available(cwd)
    result = "r" + get_svn_revision(cwd)
    if svn_local_changes_are_present(cwd):
        result += " (local changes present)"
    return result


def svn_commands_are_available(cwd=None):
    try:
        get_svn_revision(cwd)
    except subprocess.CalledProcessError:
        return False
    return True


def check_that_svn_commands_are_available(cwd=None):
    if not svn_commands_are_available(cwd):
        mesg = "Could not run svn. Is the command available on PATH? Is the script called from a repo?"
        raise RuntimeError(mesg)


def get_svn_revision(cwd=None):
    command = ["svn", "info", "--show-item", "revision"]
    output = subprocess.check_output(command, cwd=cwd, universal_newlines=True)
    # Remove trailing newline
    return output.strip()


def svn_local_changes_are_present(cwd=None):
    """
    Return true if the repo contains changes that have been made after the last commit.
    Info from here: https://rubyinrails.com/2014/01/11/svn-command-to-check-modified-files/
    """
    command = ["svn", "status"]
    output = subprocess.check_output(command, cwd=cwd, universal_newlines=True)
    # Status code for file Added, Deleted, Modified, in Conflict or missing
    regexp = re.compile(r"\n[ADMC!] ")
    return regexp.search(output) is not None
