# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import fnmatch
import time
from pathlib import Path
from threading import Lock

# Third party libraries
from vunit.color_printer import COLOR_PRINTER, NO_COLOR_PRINTER
from vunit.test.list import TestList
from vunit.test.report import TestReport, TestResult
from vunit.test.runner import TestRunner

# First party libraries
from tsfpga.system_utils import create_directory, read_last_lines_of_file


class BuildProjectList:

    """
    Interface to handle a list of FPGA build projects.
    Enables building many projects in parallel.
    """

    def __init__(
        self, modules, project_filters=None, include_netlist_not_top_builds=False, no_color=False
    ):
        """
        Arguments:
            modules (list(BaseModule)): Module objects that can define build projects.
            project_filters (list(str)): Project name filters. Can use wildcards (*).
                Leave empty for all.
            include_netlist_not_top_builds (bool): Set True to get only netlist builds,
                instead of only top level builds.
            no_color (bool): Disable color in printouts.
        """
        self._modules = modules
        self._no_color = no_color
        self.projects = list(
            self._iterate_projects(project_filters, include_netlist_not_top_builds)
        )

        if not self.projects:
            print(f"No projects matched this filter: {' '.join(project_filters)}")

    def __str__(self):
        """
        Returns a string with a description list of the projects.
        """
        result = "\n".join([str(project) for project in self.projects])
        result += "\n"
        result += "\n"
        result += f"Listed {len(self.projects)} builds"
        return result

    def create(self, projects_path, num_parallel_builds, **kwargs):
        """
        Create build project on disk for all the projects in the list.

        Arguments:
            projects_path (pathlib.Path): The projects will be placed here.
            num_parallel_builds (int): The number of projects that will be created in
                parallel.
            kwargs: Other arguments as accepted by :meth:`.VivadoProject.create`.

                .. Note::
                    Argument ``project_path`` can not be set, it is set by this class
                    based on the ``project_paths`` argument to this function.

        Returns:
            bool: True if everything went well.
        """
        build_wrappers = []
        for project in self.projects:
            build_wrapper = BuildProjectCreateWrapper(project, **kwargs)
            build_wrappers.append(build_wrapper)

        return self._run_build_wrappers(
            projects_path=projects_path,
            build_wrappers=build_wrappers,
            num_parallel_builds=num_parallel_builds,
        )

    def create_unless_exists(self, projects_path, num_parallel_builds, **kwargs):
        """
        Create build project for all the projects in the list, unless the project already
        exists.

        Arguments:
            projects_path (pathlib.Path): The projects will be placed here.
            num_parallel_builds (int): The number of projects that will be created in
                parallel.
            kwargs: Other arguments as accepted by :meth:`.VivadoProject.create`.

                .. Note::
                    Argument ``project_path`` can not be set, it is set by this class
                    based on the ``project_paths`` argument to this function.

        Returns:
            bool: True if everything went well.
        """
        build_wrappers = []
        for project in self.projects:
            if not (projects_path / project.name / "project").exists():
                build_wrapper = BuildProjectCreateWrapper(project, **kwargs)
                build_wrappers.append(build_wrapper)

        if not build_wrappers:
            # Return straight away if no projects need to be created. To avoid extra
            # "No tests were run!" printout from creation step that is very misleading.
            return True

        return self._run_build_wrappers(
            projects_path=projects_path,
            build_wrappers=build_wrappers,
            num_parallel_builds=num_parallel_builds,
        )

    def build(
        self,
        projects_path,
        num_parallel_builds,
        num_threads_per_build,
        output_path=None,
        collect_artifacts=None,
        **kwargs,
    ):
        """
        Build all the projects in the list.

        Arguments:
            projects_path (pathlib.Path): The projects will be placed here.
            num_parallel_builds (int): The number of projects that will be built in
                parallel.
            num_threads_per_build (int): The number threads that will be used for each
                parallel build process.
            output_path (pathlib.Path): Where the artifacts should be placed.
            collect_artifacts (`function`): Callback to collect artifacts. Takes two named
                arguments:

                |  **project** (:class:`.VivadoProject`): The project that is being built.

                |  **output_path** (pathlib.Path): Where the artifacts should be placed.


                | Must return True.
            kwargs: Other arguments as accepted by :meth:`.VivadoProject.build`.

                .. Note::
                    Argument ``project_path`` can not be set, it is set by this class
                    based on the ``project_paths`` argument to this function.

                    Argument ``num_threads`` is set by the ``num_threads_per_build``
                    argument to this function. This naming difference is done to avoid
                    confusion with regards to ``num_parallel_builds``.


        Returns:
            bool: True if everything went well.
        """
        if collect_artifacts:
            thread_safe_collect_artifacts = ThreadSafeCollectArtifacts(
                collect_artifacts
            ).collect_artifacts
        else:
            thread_safe_collect_artifacts = None

        build_wrappers = []
        for project in self.projects:
            if output_path:
                this_projects_output_path = output_path.resolve() / project.name
            else:
                this_projects_output_path = projects_path / project.name

            build_wrapper = BuildProjectBuildWrapper(
                project,
                output_path=this_projects_output_path,
                collect_artifacts=thread_safe_collect_artifacts,
                num_threads=num_threads_per_build,
                **kwargs,
            )
            build_wrappers.append(build_wrapper)

        return self._run_build_wrappers(
            projects_path=projects_path,
            build_wrappers=build_wrappers,
            num_parallel_builds=num_parallel_builds,
        )

    def open(self, projects_path):
        """
        Open the projects in EDA GUI.

        Arguments:
            projects_path (pathlib.Path): The projects are placed here.

        Returns:
            bool: True if everything went well.
        """
        build_wrappers = []
        for project in self.projects:
            build_wrapper = BuildProjectOpenWrapper(project)
            build_wrappers.append(build_wrapper)

        return self._run_build_wrappers(
            projects_path=projects_path,
            build_wrappers=build_wrappers,
            # For open there is no performance limitation. Set a high value.
            num_parallel_builds=20,
        )

    def _run_build_wrappers(self, projects_path, build_wrappers, num_parallel_builds):
        if not build_wrappers:
            # Return straight away if no builds are supplied
            return True

        start_time = time.time()

        color_printer = NO_COLOR_PRINTER if self._no_color else COLOR_PRINTER
        report = BuildReport(printer=color_printer)

        test_list = TestList()
        for build_wrapper in build_wrappers:
            test_list.add_test(build_wrapper)

        verbosity = BuildRunner.VERBOSITY_QUIET
        test_runner = BuildRunner(
            report=report,
            output_path=projects_path,
            verbosity=verbosity,
            num_threads=num_parallel_builds,
        )
        test_runner.run(test_list)

        all_builds_ok = report.all_ok()
        report.set_real_total_time(time.time() - start_time)

        # True if the builds are for the "build" step (not "create" or "open")
        builds_are_build_step = isinstance(build_wrappers[0], BuildProjectBuildWrapper)
        # If we are building, we should print the summary that is at the end of the console output.
        # (however if we are creating or opening a project we should not print anything extra).
        # However if anything has failed, we should also print.
        if builds_are_build_step:
            # The length of the build summary depends on if we are working with netlist builds or
            # regular ones, so set the length given by one of the project objects.
            report.set_report_length(build_wrappers[0].build_result_report_length)
        if builds_are_build_step or not all_builds_ok:
            report.print_str()

        return all_builds_ok

    def _iterate_projects(self, project_filters, include_netlist_not_top_builds):
        available_projects = []
        for module in self._modules:
            available_projects += module.get_build_projects()

        for project in available_projects:
            if project.is_netlist_build == include_netlist_not_top_builds:
                if not project_filters:
                    yield project
                else:
                    for project_filter in project_filters:
                        if fnmatch.filter([project.name], project_filter):
                            yield project

                            # Do not continue with further filters if we have already matched this
                            # project.
                            # Multiple filters might match the same project, and multiple objects
                            # of the same project will break build
                            break


class BuildProjectCreateWrapper:

    """
    Wrapper to create a build project, for usage in the build runner.
    Mimics a VUnit test object.
    """

    def __init__(self, project, **kwargs):
        self.name = project.name
        self._project = project
        self._create_arguments = kwargs

    # pylint: disable=unused-argument
    def run(self, output_path, read_output):
        """
        VUnit test runner sends another argument "read_output" which we don't use.
        """
        this_projects_path = Path(output_path) / "project"
        return self._project.create(project_path=this_projects_path, **self._create_arguments)


class BuildProjectBuildWrapper:

    """
    Wrapper to build a project, for usage in the build runner.
    Mimics a VUnit test object.
    """

    def __init__(self, project, collect_artifacts, **kwargs):
        self.name = project.name
        self._project = project
        self._collect_artifacts = collect_artifacts
        self._build_arguments = kwargs

    # pylint: disable=unused-argument
    def run(self, output_path, read_output):
        """
        VUnit test runner sends another argument "read_output" which we don't use.
        """
        this_projects_path = Path(output_path) / "project"
        build_result = self._project.build(project_path=this_projects_path, **self._build_arguments)

        if not build_result.success:
            self._print_build_result(build_result)
            return build_result.success

        # Proceed to artifact collection only if build succeeded.
        if self._collect_artifacts is not None:
            if not self._collect_artifacts(
                project=self._project, output_path=self._build_arguments["output_path"]
            ):
                build_result.success = False

        # Print size at the absolute end
        self._print_build_result(build_result)
        return build_result.success

    @staticmethod
    def _print_build_result(build_result):
        build_report = build_result.report()
        if build_report:
            # Add an empty line before the build result report, to have margin in how many lines are
            # printed. See the comments in BuildResult for an explanation.
            print()
            print(build_report)

    @property
    def build_result_report_length(self):
        """
        The number of lines in the build_result report from this project.
        """
        # The size summary, as returned by tsfpga.vivado.project.BuildResult is a JSON formatted
        # string with one line for each utilization category.
        # For Xilinx 7 series, there are 8 categories (Total LUTs, Logic LUTs, LUTRAMs,
        # SRLs, FFs, RAMB36, RAMB18, DSP Blocks). For UltraScale series there is one
        # extra (URAM).
        # Additionally, the size summary contains three extra lines for JSON braces and a title.
        #
        # This value is enough lines so the whole summary gets printed to console.
        # For 7 series, this will mean an extra blank line before the summary.
        #
        # This is a hack. Works for now, but is far from reliable.
        length_of_size_report = 3 + 8 + 1

        if self._project.is_netlist_build:
            # The logic level distribution report is five lines, plus a title line.
            # This report is only printed for netlist builds, where there is no configured clock
            # present. If there were many clocks present in the build, the report would be longer.
            length_of_logic_level_report = 5 + 1
            return length_of_size_report + length_of_logic_level_report

        return length_of_size_report


class BuildProjectOpenWrapper:

    """
    Wrapper to open a build project, for usage in the build runner.
    Mimics a VUnit test object.
    """

    def __init__(self, project):
        self.name = project.name
        self._project = project

    # pylint: disable=unused-argument
    def run(self, output_path, read_output):
        """
        VUnit test runner sends another argument "read_output" which we don't use.
        """
        this_projects_path = Path(output_path) / "project"
        return self._project.open(project_path=this_projects_path)


class BuildRunner(TestRunner):

    """
    Build runner that mimics a VUnit TestRunner. Most things are used as they are in the
    base class, but some behavior is overridden.
    """

    def _create_test_mapping_file(self, test_suites):
        """
        Do not create this file.

        We do not need it since folder name is the same as project name.
        """

    def _get_output_path(self, test_suite_name):
        """
        Output folder name is the same as the project name.

        Original function adds a hash at the end of the folder name.
        We do not want that necessarily.
        """
        return str(Path(self._output_path) / test_suite_name)

    @staticmethod
    def _prepare_test_suite_output_path(output_path):
        """
        Create the directory unless it already exists.

        Original function wipes the path before running a test. We do not want to do that
        since e.g. a Vivado project takes a long time to create and might contain a state
        that the user wants to keep.
        """
        create_directory(Path(output_path), empty=False)


class ThreadSafeCollectArtifacts:

    """
    A thread-safe wrapper around a user-supplied function that makes sure the function
    is not launched more than once at the same time. When two builds finish at the
    same time, race conditions can arise depending on what the function does.

    Note that this is a VERY fringe case, since builds usually take >20 minutes, and the
    collection probably only takes a few seconds. But it happens sometimes with the tsfpga
    example projects which are identical and quite fast (roughly three minutes).
    """

    def __init__(self, collect_artifacts):
        self._collect_artifacts = collect_artifacts
        self._lock = Lock()

    def collect_artifacts(self, project, output_path):
        with self._lock:
            return self._collect_artifacts(project=project, output_path=output_path)


class BuildReport(TestReport):
    def add_result(self, *args, **kwargs):
        """
        Add a a test result.

        Inherited and adapted from the VUnit function. Uses a different Result class.
        """
        result = BuildResult(*args, **kwargs)
        self._test_results[result.name] = result
        self._test_names_in_order.append(result.name)

    def set_report_length(self, report_length_lines):
        for test_result in self._test_results.values():
            test_result.set_report_length(report_length_lines)

    def print_latest_status(self, total_tests):
        """
        This method is called for each build when it should print its result just as it finished,
        but other builds may not be finished yet.

        Inherited and adapted from the VUnit function:
        * Removed support for the "skipped" result.
        * Do not use abbreviations in the printout.
        * Use f-strings.
        """
        result = self._last_test_result()
        passed, failed, _ = self._split()

        if result.passed:
            self._printer.write("pass", fg="gi")
        elif result.failed:
            self._printer.write("fail", fg="ri")
        else:
            assert False

        count_summary = f"pass={len(passed)} fail={len(failed)} total={total_tests}"
        self._printer.write(f" ({count_summary}) {result.name} ({result.time:.1f} seconds)\n")


class BuildResult(TestResult):
    report_length_lines = None

    def _print_output(self, printer, num_lines):
        """
        Print the last lines from the output file.
        """
        output_tail = read_last_lines_of_file(Path(self._output_file_name), num_lines=num_lines)
        printer.write(output_tail)

    def set_report_length(self, report_length_lines):
        self.report_length_lines = report_length_lines

    def print_status(self, printer, padding=0):
        """
        This method is called for each build when it should print its result in the "Summary" at
        the end when all builds have finished.

        Inherited and adapted from the VUnit function.
        """
        if self.passed and self.report_length_lines is not None:
            # Build passed, print build summary of the specified length. The length is only
            # set if this is a "build" result (not "create" or "open").
            self._print_output(printer, num_lines=self.report_length_lines)
        else:
            # The build failed, which can either be caused by
            # 1. IDE build failure
            # 2. IDE build succeeded, but post build hook, or size checkers failed.
            # 3. Other python error (directory already exists, ...)
            # In the case of IDE build failed, we want a significant portion of the output, to be
            # able to see an indication of what failed. In the case of size checkers, we want to see
            # all the printouts from all checkers, to see which one failed. Since there are at most
            # eight resource categories, it is reasonable to assume that there will never be more
            # than eight size checkers.
            self._print_output(printer, num_lines=25)

        # Print the regular output from the VUnit class.
        # A little extra margin between build name and execution time makes the output more readable
        super().print_status(printer, padding + 2)
        # Add an empty line between each build, for readability.
        printer.write("\n")
