# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from git.repo import Repo

from .hdl_file import HdlFile
from .system_utils import path_relative_to

if TYPE_CHECKING:
    from collections.abc import Iterable

    from git.diff import DiffIndex
    from vunit.ui import VUnit

    from .module import BaseModule
    from .module_list import ModuleList

# VHDL, Verilog and SystemVerilog.
_FILE_ENDINGS = HdlFile.file_endings


class GitSimulationSubset:
    """
    Find a subset of testbenches to simulate based on the local git
    tree compared to a reference branch.
    """

    # To match file name "regs_NAME.toml/json/yaml".
    _re_register_data_filename = re.compile(r"^regs_(.+)\.[a-z]+$")

    def __init__(
        self, repo_root: Path, reference_branch: str, modules: ModuleList | None = None
    ) -> None:
        """
        Arguments:
            repo_root: Root directory where git commands will be run.
            reference_branch: What git branch to compare against, when finding what files
                have changed.
                Typically "origin/main" or "origin/master".
            modules: Provide this argument to make the class look for changes in the modules'
                register data files also.
                If any changes are found, the register HDL files, and any HDL files that depend
                on them, will be added to the test pattern.
        """
        self._repo_root = repo_root
        self._reference_branch = reference_branch
        self._modules = modules

    def update_test_pattern(self, vunit_proj: VUnit) -> set[Path]:
        """
        Update VUnit project test pattern to include testbenches depending on files
        that have changes in the local git tree compared to the reference branch.

        Arguments:
            vunit_proj: The VUnit project that will be updated.

        Returns:
            The HDL files that were found to have a git diff.
        """
        hdl_files = self.get_hdl_file_diff()
        vunit_proj.update_test_pattern(include_dependent_on=hdl_files)

        return hdl_files

    def get_hdl_file_diff(self) -> set[Path]:
        """
        Get the HDL files that have changes in the the local git tree compared to
        the reference branch.
        """
        repo = Repo(self._repo_root)

        head_commit = repo.head.commit
        reference_commit = repo.commit(rev=self._reference_branch)

        # Local uncommitted changed
        working_tree_changes = head_commit.diff(None)

        # Changes in the git log compared to the reference commit
        history_changes = head_commit.diff(reference_commit)

        all_changes: DiffIndex[Any] = working_tree_changes + history_changes

        return self._get_hdl_files(diffs=all_changes)

    def _get_hdl_files(self, diffs: DiffIndex[Any]) -> set[Path]:
        """
        Return HDL files that have been changed (added/renamed/modified/deleted) within any
        of the ``diffs`` commits.

        Will also try to find HDL files that depend on generated register artifacts that
        have changed.
        """
        files = set()

        def add_register_artifacts_if_match(
            diff_path: Path, module_register_data_file: Path, module: BaseModule
        ) -> None:
            """
            Note that Path.__eq__ does not do normalization of paths.
            If one argument is relative and the other is absolute, they will not be equal.
            Hence, it is important that both paths are resolved before comparison.
            """
            if diff_path != module_register_data_file:
                return

            re_match = self._re_register_data_filename.match(module_register_data_file.name)
            if re_match is None:
                raise ValueError("Register data file does not use the expected naming convention")

            register_list_name = re_match.group(1)
            regs_pkg_path = module.register_synthesis_folder / f"{register_list_name}_regs_pkg.vhd"

            # It is okay to add only the base register package, since all other
            # register artifacts depend on it.
            # This file will typically not exist yet in a CI flow, so it doesn't make sense to
            # assert for its existence.
            files.add(regs_pkg_path)

        for diff_path in self._get_diff_paths(diffs=diffs):
            if diff_path.name.endswith(_FILE_ENDINGS):
                files.add(diff_path)

            elif self._modules is not None:
                for module in self._modules:
                    module_register_data_file = module.register_data_file

                    if isinstance(module_register_data_file, list):
                        # In case users implement a sub-class of BaseModule that has multiple
                        # register lists.
                        # This is not a standard use case that we recommend or support in general,
                        # but we support it here for convenience.
                        for data_file in module_register_data_file:
                            add_register_artifacts_if_match(
                                diff_path=diff_path,
                                module_register_data_file=data_file,
                                module=module,
                            )

                    else:
                        add_register_artifacts_if_match(
                            diff_path=diff_path,
                            module_register_data_file=module_register_data_file,
                            module=module,
                        )

        self._print_file_list(files=files)
        return files

    def _get_diff_paths(self, diffs: DiffIndex[Any]) -> Iterable[Path]:
        """
        * If a file is modified, ``a_path`` and ``b_path`` are set and point to the same file.
        * If a file is added, ``a_path`` is None and ``b_path`` points to the newly added file.
        * If a file is deleted, ``b_path`` is None and ``a_path`` points to the old deleted file.
          We still include the 'a_path' in in this case, since we want to catch
          if any files depend on the deleted file, which would be an error.
          This mechanism probably does not work, since VUnit dependency scanner does not know what
          was in that file.
          But from the perspective of this method, returning the deleted file is still correct.
        """
        result = set()

        for diff in diffs:
            if diff.a_path is not None:
                result.add(Path(diff.a_path).resolve())

            if diff.b_path is not None:
                result.add(Path(diff.b_path).resolve())

        return result

    @staticmethod
    def _print_file_list(files: set[Path]) -> None:
        if not files:
            return

        print("Found git diff related to the following files:")

        sorted_files = sorted(files)
        cwd = Path.cwd()
        for path in sorted_files:
            relative_path = path_relative_to(path=path, other=cwd)
            print(f"  {relative_path}")
        print()
