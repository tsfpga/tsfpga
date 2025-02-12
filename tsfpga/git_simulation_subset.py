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

if TYPE_CHECKING:
    from collections.abc import Iterable

    from git.diff import DiffIndex
    from vunit.ui import VUnit
    from vunit.ui.source import SourceFile

    from .module import BaseModule
    from .module_list import ModuleList

VHDL_FILE_ENDINGS = HdlFile.file_endings_mapping[HdlFile.Type.VHDL]


class GitSimulationSubset:
    """
    Find a subset of testbenches to simulate based on git history.
    """

    # Should work with
    # * tb_<name>.vhd
    # * <name>_tb.vhd
    # and possibly .vhdl as file extension.
    _re_tb_filename = re.compile(r"^(tb_.+\.vhdl?)|(.+\_tb.vhdl?)$")
    # Should work with .toml, .json, .yaml, etc.
    _re_register_data_filename = re.compile(r"^regs_(.+)\.[a-z]+$")

    def __init__(
        self,
        repo_root: Path,
        reference_branch: str,
        vunit_proj: VUnit,
        modules: ModuleList | None = None,
        vunit_preprocessed_path: Path | None = None,
    ) -> None:
        """
        Arguments:
            repo_root: Root directory where git commands will be run.
            reference_branch: What git branch to compare against, when finding what files have
                changed. Typically "origin/main" or "origin/master".
            vunit_proj: A vunit project with all source files and testbenches added. Will be used
                for dependency scanning.
            modules: A list of modules that are included in the VUnit project.

                When this argument is provided, this class will look for changes in the modules'
                register data files, and simulate the testbenches that depend on register artifacts
                in case of any changes.

                This argument **must**  be supplied if VUnit preprocessing is enabled.
            vunit_preprocessed_path: If location/check preprocessing is enabled
                in your VUnit project, supply the path to ``vunit_out/preprocessed``.
        """
        self._repo_root = repo_root
        self._reference_branch = reference_branch
        self._vunit_proj = vunit_proj
        self._modules = modules
        self._vunit_preprocessed_path = vunit_preprocessed_path

    def find_subset(self) -> list[tuple[str, str]]:
        """
        Return all testbenches that have changes, or depend on files that have changes.

        Return:
            The testbench names and their corresponding library names.
            A list of tuples ("testbench name", "library name").
        """
        diff_files = self._find_diff_vhd_files()

        if self._vunit_preprocessed_path:
            # If preprocessing is enabled, VUnit's dependency graph is based on the files that
            # are in the vunit_out/preprocessed folder, not in the file's original location.
            # So manipulate the paths to point there.
            diff_files = self._get_preprocessed_file_locations(diff_files)
            self._print_file_list("Resolved diff file locations to be", diff_files)

        # Find all testbench files that are available
        testbenches = self._find_testbenches()

        # Gather the testbenches that depend on any files that have diffs
        testbenches_to_run = []
        for testbench_source_file in testbenches:
            if self._source_file_depends_on_files(
                source_file=testbench_source_file,
                files=diff_files,
            ):
                testbench_file_name = Path(testbench_source_file.name).stem
                testbenches_to_run.append((testbench_file_name, testbench_source_file.library.name))

        return testbenches_to_run

    def _find_diff_vhd_files(self) -> set[Path]:
        repo = Repo(self._repo_root)

        head_commit = repo.head.commit
        reference_commit = repo.commit(self._reference_branch)

        # Local uncommitted changed
        working_tree_changes = head_commit.diff(None)

        # Changes in the git log compared to the reference commit
        history_changes = head_commit.diff(reference_commit)

        all_changes: DiffIndex[Any] = working_tree_changes + history_changes

        return self._get_vhd_files(diffs=all_changes)

    def _get_vhd_files(self, diffs: DiffIndex[Any]) -> set[Path]:
        """
        Return VHDL files that have been changed (added/renamed/modified/deleted) within any
        of the ``diffs`` commits.

        Will also try to find VHDL files that depend on generated register artifacts that
        have changed.
        """
        files = set()

        def add_register_artifacts_if_match(
            diff_path: Path, module_register_data_file: Path, module: BaseModule
        ) -> None:
            """
            Note that Path.__eq__ does not do normalization of paths.
            If one argument is a relative path and the other is an absolute path, they will not
            be considered equal.
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

        for diff_path in self._iterate_diff_paths(diffs=diffs):
            if diff_path.name.endswith(VHDL_FILE_ENDINGS):
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

        self._print_file_list("Found git diff related to the following files", files)
        return files

    def _iterate_diff_paths(self, diffs: DiffIndex[Any]) -> Iterable[Path]:
        """
        * If a file is modified, ``a_path`` and ``b_path`` are set and point to the same file.
        * If a file is added, ``a_path`` is None and ``b_path`` points to the newly added file.
        * If a file is deleted, ``b_path`` is None and ``a_path`` points to the old deleted file.
          We still include the 'a_path' in in this case, since we want to catch
          if any files depend on the deleted file, which would be an error.
        """
        for diff in diffs:
            if diff.a_path is not None:
                yield Path(diff.a_path).resolve()

            if diff.b_path is not None:
                yield Path(diff.b_path).resolve()

    def _get_preprocessed_file_locations(self, vhd_files: set[Path]) -> set[Path]:
        """
        Find the location of a VUnit preprocessed file, based on the path in the modules tree.
        Not all VHDL files are included in the simulation projects (e.g. often files that depend
        on IP cores are excluded), hence files that can not be found in any module's simulation
        files are ignored.
        """
        if self._modules is None:
            raise ValueError("Modules must be supplied when VUnit preprocessing is enabled")

        result = set()
        for vhd_file in vhd_files:
            library_name = self._get_library_name_from_path(vhd_file)

            if library_name is not None:
                preprocessed_file = self._vunit_preprocessed_path / library_name / vhd_file.name
                if not preprocessed_file.exists():
                    raise FileNotFoundError("Could not find file:", preprocessed_file)

                result.add(preprocessed_file)

        return result

    def _get_library_name_from_path(self, vhd_file: Path) -> str | None:
        """
        Returns: Library name for the given file path.
            Will return None if no library can be found.
        """
        # Ignore that '_modules' is type 'Path | None', since we only come
        # if it is not 'None'.
        for module in self._modules:
            for module_hdl_file in module.get_simulation_files(include_ip_cores=True):
                if module_hdl_file.path.name == vhd_file.name:
                    return module.library_name

        print(f"Could not find library for file {vhd_file}. It will be skipped.")
        return None

    def _find_testbenches(self) -> list[SourceFile]:
        """
        Find all testbench files that are available in the VUnit project.
        """
        result = []
        for source_file in self._vunit_proj.get_source_files():
            source_file_path = Path(source_file.name)
            if not source_file_path.exists():
                raise FileNotFoundError("Could not find file:", source_file_path)

            # The file is considered a testbench if it follows the tb naming pattern
            if self._re_tb_filename.match(source_file_path.name) is not None:
                result.append(source_file)

        return result

    def _source_file_depends_on_files(self, source_file: SourceFile, files: set[Path]) -> bool:
        """
        Return True if the source file depends on any of the files.
        """
        # Note that this includes the source_file itself.
        implementation_subset = self._vunit_proj.get_implementation_subset([source_file])

        # Convert to a set of absolute Paths, for comparison with "files" which is of that type.
        source_file_dependencies = {
            Path(implementation_file.name).resolve()
            for implementation_file in implementation_subset
        }

        intersection = source_file_dependencies & files
        if not intersection:
            return False

        self._print_file_list(
            f"Testbench {source_file.name} depends on the following files which have a diff",
            intersection,
        )
        return True

    @staticmethod
    def _print_file_list(title: str, files: set[Path]) -> None:
        if not files:
            return

        sorted_files = sorted(files)

        print(f"{title}:")
        for file_path in sorted_files:
            print(f"  {file_path}")
        print()
