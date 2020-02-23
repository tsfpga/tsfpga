# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from unittest import mock

from tsfpga.svn_utils import svn_local_changes_are_present

# SVN is pretty much impossible to work with. Most of the functions are untested.


@mock.patch("subprocess.check_output", autospec=True)
def test_svn_local_changes_are_present(check_output):
    check_output.return_value = """
?       .vscode
?       build
"""
    assert not svn_local_changes_are_present()

    check_output.return_value = """
?       .vscode
M       build.py
?       build
"""
    assert svn_local_changes_are_present()

    check_output.return_value = """
?       .vscode
!       build.py
?       build
"""
    assert svn_local_changes_are_present()
