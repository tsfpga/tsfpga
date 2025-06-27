# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from unittest.mock import MagicMock, Mock, patch

from vunit.ui import VUnit

from tsfpga.git_simulation_subset import GitSimulationSubset
from tsfpga.module import get_modules
from tsfpga.system_utils import create_file


def test_find_subset(tmp_path):
    """
    Set up a scenario with a few files that have diffs and a few files that do not.
    """
    module_paths = tmp_path / "modules"

    vhd_with_diff = create_file(module_paths / "foo" / "file_with_diff.vhdl")
    verilog_with_diff = create_file(module_paths / "foo" / "file_with_diff.v")
    create_file(module_paths / "foo" / "file_with_no_diff.vhd")
    tb_vhd_with_diff = create_file(module_paths / "foo" / "tb_file_with_diff.vhd")
    create_file(module_paths / "foo" / "file1_with_no_diff_tb.vhdl")
    create_file(module_paths / "foo" / "file2_with_no_diff_tb.vhdl")
    create_file(module_paths / "foo" / "file3_with_no_diff_tb.vhdl")
    regs_toml_with_diff = create_file(module_paths / "bar" / "regs_bar.toml")
    regs_pkg_vhd_untracked = create_file(module_paths / "bar" / "regs_src" / "bar_regs_pkg.vhd")

    modules = get_modules(modules_folder=module_paths)

    git_simulation_subset = GitSimulationSubset(
        repo_root=tmp_path, reference_branch="origin/master", modules=modules
    )

    with patch("tsfpga.git_simulation_subset.Repo", autospec=True) as mocked_repo:
        repo = mocked_repo.return_value
        head_commit = repo.head.commit

        reference_commit = repo.commit.return_value

        def diff_commit(arg):
            """
            Return the files that have diffs. One or the other depending on what the argument
            (reference commit, or None=local tree) is.
            """
            if arg is None:
                diff = MagicMock()
                diff.b_path = tb_vhd_with_diff
                return [diff]

            if arg is reference_commit:
                diff1 = MagicMock()
                diff1.b_path = vhd_with_diff

                diff2 = MagicMock()
                diff2.b_path = verilog_with_diff

                diff3 = MagicMock()
                diff3.b_path = regs_toml_with_diff

                return [diff1, diff2, diff3]

            raise AssertionError

        head_commit.diff.side_effect = diff_commit

        vunit_proj = Mock(spec=VUnit)

        git_simulation_subset.update_test_pattern(vunit_proj=vunit_proj)

        repo.commit.assert_called_once_with("origin/master")

        vunit_proj.update_test_pattern.assert_called_once_with(
            include_dependent_on={
                vhd_with_diff,
                tb_vhd_with_diff,
                verilog_with_diff,
                regs_pkg_vhd_untracked,
            }
        )
