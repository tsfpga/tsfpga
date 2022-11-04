# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from unittest import mock

# First party libraries
from tsfpga.svn_utils import find_svn_files, svn_local_changes_are_present
from tsfpga.system_utils import create_file

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


@mock.patch("subprocess.check_output", autospec=True)
def test_find_svn_files(check_output, tmp_path):
    apa_txt = create_file(tmp_path / "apa.txt")
    hest_txt = create_file(tmp_path / "stuff" / "hest.txt")
    zebra_vhd = create_file(tmp_path / "stuff" / "zebra.vhd")
    zebra_pdf = create_file(tmp_path / "things" / "zebra.pdf")

    check_output.return_value = """\
            104134   104134 lukas.vik    .
?                                        .pytest_cache
?                                        .vscode
?                                        build
            104134   104134 lukas.vik    apa.txt

Performing status on external item at 'stuff':
            104134   103740 lukas.vik    stuff
M           104134   103740 lukas.vik    stuff/hest.txt
            104134   103740 lukas.vik    stuff/zebra.vhd

Performing status on external item at 'things':
            104134   103740 lukas.vik    things
M   X       104134   103740 lukas.vik    things/zebra.pdf
"""
    assert set(find_svn_files(tmp_path)) == {apa_txt, hest_txt, zebra_pdf, zebra_vhd}

    # Filter file endings include
    assert set(find_svn_files(tmp_path, file_endings_include="txt")) == {apa_txt, hest_txt}
    assert set(find_svn_files(tmp_path, file_endings_include=("txt", "vhd"))) == {
        apa_txt,
        hest_txt,
        zebra_vhd,
    }

    # Filter file endings avoid
    assert set(find_svn_files(tmp_path, file_endings_avoid="txt")) == {zebra_vhd, zebra_pdf}
    assert set(find_svn_files(tmp_path, file_endings_avoid=("txt", "vhd"))) == {zebra_pdf}

    # Filter exclude
    assert set(find_svn_files(tmp_path, excludes=[zebra_vhd.parent])) == {apa_txt, zebra_pdf}
    assert set(find_svn_files(tmp_path, excludes=[zebra_vhd.parent, zebra_pdf.parent])) == {apa_txt}
