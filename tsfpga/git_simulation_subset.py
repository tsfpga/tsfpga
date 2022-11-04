# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import re
from pathlib import Path

# Third party libraries
from git import Repo


class GitSimulationSubset:
    """
    Find a subset of testbenches to simulate based on git history.
    """

    _re_tb_filename = re.compile(r"(tb_.+\.vhd)|(.+\_tb.vhd)")

    def __init__(
        self, repo_root, reference_branch, vunit_proj, vunit_preprocessed_path=None, modules=None
    ):
        """
        Arguments:
            repo_root (pathlib.Path): Root directory where git commands will be run.
            reference_branch (str): What git branch to compare against, when finding what files have
                changed. Typically "origin/main" or "origin/master".
            vunit_proj: A vunit project with all source files and testbenches added. Will be used
                for dependency scanning.
            vunit_preprocessed_path (pathlib.Path): If location/check preprocessing is enabled
                in your VUnit project, supply the path to vunit_out/preprocessed.
            modules (ModuleList): A list of modules that are included in the VUnit project. Must be
                supplied only if preprocessing is enabled.
        """
        self._repo_root = repo_root
        self._reference_branch = reference_branch
        self._vunit_proj = vunit_proj
        self._vunit_preprocessed_path = vunit_preprocessed_path
        self._modules = modules

        if (vunit_preprocessed_path is not None) != (modules is not None):
            raise ValueError("Can not supply only one of vunit_preprocessed_path and modules")

    def find_subset(self):
        """
        Return all testbenches that have changes, or depend on files that have changes.

        Return:
            list(tuple(str, str)): The testbench names and their corresponding library names. A list
            of tuples ("testbench name", "library name").
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
        for testbench_source_file, library_name in testbenches:
            if self._source_file_depends_on_files(
                source_file=testbench_source_file,
                files=diff_files,
            ):
                testbench_file_name = Path(testbench_source_file.name).stem
                testbenches_to_run.append((testbench_file_name, library_name))

        return testbenches_to_run

    def _find_diff_vhd_files(self):
        repo = Repo(self._repo_root)

        head_commit = repo.head.commit
        reference_commit = repo.commit(self._reference_branch)

        # Local uncommitted changed
        working_tree_changes = head_commit.diff(None)

        # Changes in the git log compared to the reference commit
        history_changes = head_commit.diff(reference_commit)

        return self._iterate_vhd_file_diffs(diffs=working_tree_changes + history_changes)

    def _iterate_vhd_file_diffs(self, diffs):
        """
        Return the currently existing files that have been changed (added/renamed/modified)
        within any of the diffs commits.

        Returns a set of Paths.
        """
        files = set()

        for diff in diffs:
            # The diff contains "a" -> "b" changes information. In case of file deletion, a_path
            # will be set but not b_path. Removed files are not included by this method.
            if diff.b_path is not None:
                b_path = Path(diff.b_path)

                # A file can be changed in an early commit, but then removed/renamed in a
                # later commit. Include only files that are currently existing.
                if b_path.exists():
                    if b_path.name.endswith(".vhd"):
                        files.add(b_path.resolve())

        self._print_file_list("Found git diff in the following files", files)
        return files

    def _get_preprocessed_file_locations(self, vhd_files):
        """
        Find the location of a VUnit preprocessed file, based on the path in the modules tree.
        Not all VHDL files are included in the simulation projects (e.g. often files that depend
        on IP cores are excluded), hence files that can not be found in any module's simulation
        files are ignored.
        """
        result = set()
        for vhd_file in vhd_files:
            library_name = self._get_library_name_from_path(vhd_file)

            if library_name is not None:
                preprocessed_file = self._vunit_preprocessed_path / library_name / vhd_file.name
                assert preprocessed_file.exists(), preprocessed_file

                result.add(preprocessed_file)

        return result

    def _get_library_name_from_path(self, vhd_file):
        """
        Returns (str): Library name for the given file path.
            Will return None if no library can be found.
        """
        for module in self._modules:
            for module_hdl_file in module.get_simulation_files(include_ip_cores=True):
                if module_hdl_file.path.name == vhd_file.name:
                    return module.library_name

        print(f"Could not find library for file {vhd_file}. It will be skipped.")
        return None

    def _find_testbenches(self):
        """
        Find all testbench files that are available in the VUnit project.

        Return:
            list(tuple(``SourceFile``, str)): The VUnit SourceFile objects and library names
                for the files.
        """
        result = []
        for source_file in self._vunit_proj.get_source_files():
            source_file_path = Path(source_file.name)
            assert source_file_path.exists(), source_file_path

            # The file is considered a testbench if it follows the tb naming pattern
            if re.fullmatch(self._re_tb_filename, source_file_path.name):
                result.append((source_file, source_file.library.name))

        return result

    def _source_file_depends_on_files(self, source_file, files):
        """
        Return True if the source_file depends on any of the files.
        """
        # Note that this includes the source_file itself. Is a list of SourceFile objects.
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
    def _print_file_list(title, files):
        print(f"{title}:")
        for file_path in files:
            print(f"  {file_path}")
        print()
