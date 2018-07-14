import os
from os.path import join, exists, normpath
import subprocess

from hdl_reuse import ROOT


def get_git_commit(cwd=None):
    """
    Generally, eight to ten characters are more than enough to be unique within a project.
    The linux kernel, one of the largest projects, needs 11.
    https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection#Short-SHA-1
    """
    sha_length = 16
    if "GIT_COMMIT" in os.environ:
        return os.environ["GIT_COMMIT"][0:sha_length]

    check_that_git_commands_are_available(cwd)

    git_commit = get_git_sha(cwd)[0:sha_length]
    if git_local_changes_are_present(cwd):
        git_commit += " (local changes present)"

    return git_commit


def get_git_sha(cwd=None):
    command = ["git", "rev-parse", "HEAD"]
    output = subprocess.check_output(command, cwd=cwd, universal_newlines=True)
    return output


def git_local_changes_are_present(cwd=None):
    command = ["git", "diff-index", "--quiet", "HEAD", "--"]
    try:
        subprocess.check_call(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return True
    return False


def git_commands_are_available(cwd=None):
    command = ["git", "rev-parse", "--is-inside-work-tree"]
    try:
        subprocess.check_call(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False
    return True


def check_that_git_commands_are_available(cwd=None):
    if not git_commands_are_available(cwd):
        mesg = "Could not run git. Is the command available on PATH? Is the script called from a repo?"
        raise RuntimeError(mesg)


def find_git_files(file_ending=None):
    command = ["git", "ls-files"]
    output = subprocess.check_output(command, cwd=ROOT, universal_newlines=True)
    ls_files = output.split("\n")

    # subprocess.check_output() returns a trailing "\n". The split() call will make that an empty object at the end of the list.
    ls_files = ls_files[:-1]

    for file in ls_files:
        if file_ending is None or file.endswith(file_ending):
            # git ls-files returns paths relative to the working directory where it's called. Hence we prepend the cwd used.
            file = join(ROOT, file)
            assert exists(file)  # Make sure concatenation of relative path worked

            # normpath is necessary in windows where you can get a mix of slashes and backslashes which makes
            # path comparisons sketchy
            yield normpath(file)
