# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from unittest.mock import MagicMock, patch

# Third party libraries
import pytest

# First party libraries
from tsfpga.git_simulation_subset import GitSimulationSubset
from tsfpga.system_utils import create_file


def test_supplying_only_one_of_vunit_preprocessed_path_or_modules_should_raise_exception():
    GitSimulationSubset(repo_root=None, reference_branch=None, vunit_proj=None)
    GitSimulationSubset(
        repo_root=None,
        reference_branch=None,
        vunit_proj=None,
        vunit_preprocessed_path="dummy",
        modules="dummy",
    )

    assertion_message = "Can not supply only one of vunit_preprocessed_path and modules"

    with pytest.raises(ValueError) as exception_info:
        GitSimulationSubset(
            repo_root=None,
            reference_branch=None,
            vunit_proj=None,
            vunit_preprocessed_path="dummy",
        )
    assert str(exception_info.value) == assertion_message

    with pytest.raises(ValueError) as exception_info:
        GitSimulationSubset(
            repo_root=None,
            reference_branch=None,
            vunit_proj=None,
            modules="dummy",
        )
    assert str(exception_info.value) == assertion_message


def test_find_subset(tmp_path):  # pylint: disable=too-many-locals
    # Set up a scenario with a few files that have diffs and a few files that do not.
    # The tb without diffs will be set up so that it depends on the source file that
    # has diffs. This means that both tb's should be returned by find_subset().
    #
    # It is quite a complicated test. I am not sure that it adds a tremendous amount of value.
    # It is really just a practice in using mocks. :)
    vhd_with_diff = create_file(tmp_path / "file_with_diff.vhd")
    vhd_with_no_diff = create_file(tmp_path / "file_with_no_diff.vhd")
    tb_vhd_with_diff = create_file(tmp_path / "tb_file_with_diff.vhd")
    tb_vhd_with_no_diff = create_file(tmp_path / "tb_file_with_no_diff.vhd")

    vunit_proj = MagicMock()

    git_simulation_subset = GitSimulationSubset(
        repo_root=tmp_path, reference_branch="origin/main", vunit_proj=vunit_proj
    )

    with patch("tsfpga.git_simulation_subset.Repo", autospec=True) as mocked_repo:
        repo = mocked_repo.return_value
        head_commit = repo.head.commit

        reference_commit = repo.commit.return_value

        def diff_commit(arg):
            # Return the files that have diffs. One or the other depending on what the argument
            # (reference commit, or None=local tree) is.
            diff = MagicMock()
            if arg is None:
                diff.b_path = tb_vhd_with_diff
            elif arg is reference_commit:
                diff.b_path = vhd_with_diff
            else:
                assert False
            return [diff]

        head_commit.diff.side_effect = diff_commit

        source_file_vhd_with_diff = MagicMock()
        source_file_vhd_with_diff.name = str(vhd_with_diff)
        source_file_vhd_with_diff.library.name = "apa"

        source_file_vhd_with_no_diff = MagicMock()
        source_file_vhd_with_no_diff.name = str(vhd_with_no_diff)
        source_file_vhd_with_no_diff.library.name = "hest"

        source_file_tb_vhd_with_diff = MagicMock()
        source_file_tb_vhd_with_diff.name = str(tb_vhd_with_diff)
        source_file_tb_vhd_with_diff.library.name = "zebra"

        source_file_tb_vhd_with_no_diff = MagicMock()
        source_file_tb_vhd_with_no_diff.name = str(tb_vhd_with_no_diff)
        source_file_tb_vhd_with_no_diff.library.name = "foo"

        vunit_proj.get_source_files.return_value = [
            source_file_tb_vhd_with_diff,
            source_file_vhd_with_diff,
            source_file_vhd_with_no_diff,
            source_file_tb_vhd_with_no_diff,
        ]

        def get_implementation_subset(arg):
            if arg == [source_file_tb_vhd_with_diff]:
                # This tb, which has a diff, depends on itself and a vhd file with no diff
                return [source_file_tb_vhd_with_diff, source_file_vhd_with_no_diff]
            if arg == [source_file_tb_vhd_with_no_diff]:
                # This tb, which has no diff, depends on itself and a vhd file that does have a diff
                return [source_file_tb_vhd_with_no_diff, source_file_vhd_with_diff]
            assert False
            return None

        vunit_proj.get_implementation_subset.side_effect = get_implementation_subset

        assert git_simulation_subset.find_subset() == [
            ("tb_file_with_diff", "zebra"),
            ("tb_file_with_no_diff", "foo"),
        ]

        repo.commit.assert_called_once_with("origin/main")
