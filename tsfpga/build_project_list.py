# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

import fnmatch
import time
from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Any

from vunit.color_printer import COLOR_PRINTER, NO_COLOR_PRINTER, ColorPrinter
from vunit.test.list import TestList
from vunit.test.report import TestReport, TestResult
from vunit.test.runner import TestRunner

from tsfpga.system_utils import create_directory, read_last_lines_of_file

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from .module_list import ModuleList
    from .vivado import build_result
    from .vivado.project import VivadoProject


class BuildProjectList:
    """
    Interface to handle a list of FPGA build projects.
    Enables building many projects in parallel.
    """

    def __init__(self, projects: Sequence[VivadoProject], no_color: bool = False) -> None:
        """
        Arguments:
            projects: The FPGA build projects that will be executed.
            no_color: Disable color in printouts.
        """
        self.projects = projects
        self._no_color = no_color

    def __str__(self) -> str:
        """
        Returns a string with a description list of the projects.

        Will print some information about each project (name, generics, part, ...) so can become
        long if there are many projects present.
        An alternative in that case would be :meth:`.get_short_str`.
        """
        result = "\n".join([str(project) for project in self.projects])
        result += "\n"
        result += "\n"
        result += f"Listed {len(self.projects)} builds"

        return result

    def get_short_str(self) -> str:
        """
        Returns a short string with a description list of the projects.

        This is an alternative function that is more compact than ``__str__``.
        """
        result = "\n".join([project.name for project in self.projects])
        result += "\n"
        result += f"Listed {len(self.projects)} builds"

        return result

    def create(
        self,
        projects_path: Path,
        num_parallel_builds: int,
        **kwargs: Any,  # noqa: ANN401
    ) -> bool:
        """
        Create build project on disk for all the projects in the list.

        Arguments:
            projects_path: The projects will be placed here.
            num_parallel_builds: The number of projects that will be created in parallel.
            kwargs: Other arguments as accepted by :meth:`.VivadoProject.create`.

                .. Note::
                    Argument ``project_path`` can not be set, it is set by this class
                    based on the ``project_paths`` argument to this function.

        Return:
            True if everything went well.
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

    def create_unless_exists(
        self,
        projects_path: Path,
        num_parallel_builds: int,
        **kwargs: Any,  # noqa: ANN401
    ) -> bool:
        """
        Create build project for all the projects in the list, unless the project already
        exists.

        Arguments:
            projects_path: The projects will be placed here.
            num_parallel_builds: The number of projects that will be created in parallel.
            kwargs: Other arguments as accepted by :meth:`.VivadoProject.create`.

                .. Note::
                    Argument ``project_path`` can not be set, it is set by this class
                    based on the ``project_paths`` argument to this function.

        Return:
            True if everything went well.
        """
        build_wrappers = []
        for project in self.projects:
            if not self.get_build_project_path(
                project=project, projects_path=projects_path
            ).exists():
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
        projects_path: Path,
        num_parallel_builds: int,
        num_threads_per_build: int,
        output_path: Path | None = None,
        collect_artifacts: Callable[[VivadoProject, Path], bool] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> bool:
        """
        Build all the projects in the list.

        Arguments:
            projects_path: The projects are placed here.
            num_parallel_builds: The number of projects that will be built in parallel.
            num_threads_per_build: The number threads that will be used for each
                parallel build process.
            output_path: Where the artifacts should be placed.
                Will default to within the ``projects_path`` if not set.
            collect_artifacts: Callback to collect artifacts.
                Takes two named arguments:

                |  **project** (:class:`.VivadoProject`): The project that is being built.

                |  **output_path** (pathlib.Path): Where the build artifacts should be placed.

                | Must return True.
            kwargs: Other arguments as accepted by :meth:`.VivadoProject.build`.

                .. Note::
                    Argument ``project_path`` can not be set, it is set by this class
                    based on the ``project_paths`` argument to this function.

                    Argument ``num_threads`` is set by the ``num_threads_per_build``
                    argument to this function. This naming difference is done to avoid
                    confusion with regards to ``num_parallel_builds``.

        Return:
            True if everything went well.
        """
        if collect_artifacts:
            thread_safe_collect_artifacts = ThreadSafeCollectArtifacts(
                collect_artifacts=collect_artifacts
            ).collect_artifacts
        else:
            thread_safe_collect_artifacts = None

        build_wrappers = []
        for project in self.projects:
            project_output_path = self.get_build_project_output_path(
                project=project, projects_path=projects_path, output_path=output_path
            )

            build_wrapper = BuildProjectBuildWrapper(
                project=project,
                collect_artifacts=thread_safe_collect_artifacts,
                output_path=project_output_path,
                num_threads=num_threads_per_build,
                **kwargs,
            )
            build_wrappers.append(build_wrapper)

        return self._run_build_wrappers(
            projects_path=projects_path,
            build_wrappers=build_wrappers,
            num_parallel_builds=num_parallel_builds,
        )

    @staticmethod
    def get_build_project_path(project: VivadoProject, projects_path: Path) -> Path:
        """
        Find where the project files for a specific project will be placed.
        Arguments are the same as for :meth:`.create`.
        """
        return projects_path / project.name / "project"

    @staticmethod
    def get_build_project_output_path(
        project: VivadoProject, projects_path: Path, output_path: Path | None = None
    ) -> Path:
        """
        Find where build artifacts will be placed for a project.
        Arguments are the same as for :meth:`.build`.
        """
        if output_path:
            return output_path.resolve() / project.name

        return projects_path / project.name

    def open(self, projects_path: Path) -> bool:
        """
        Open the projects in EDA GUI.

        Arguments:
            projects_path: The projects are placed here.

        Return:
            True if everything went well.
        """
        build_wrappers = [BuildProjectOpenWrapper(project=project) for project in self.projects]

        return self._run_build_wrappers(
            projects_path=projects_path,
            build_wrappers=build_wrappers,
            # For open there is no performance limitation. Set a high value.
            num_parallel_builds=20,
        )

    def _run_build_wrappers(
        self,
        projects_path: Path,
        build_wrappers: list[BuildProjectCreateWrapper]
        | list[BuildProjectBuildWrapper]
        | list[BuildProjectOpenWrapper],
        num_parallel_builds: int,
    ) -> bool:
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

        all_builds_ok: bool = report.all_ok()
        report.set_real_total_time(time.time() - start_time)

        # True if the builds are for the "build" step (not "create" or "open")
        builds_are_build_step = isinstance(build_wrappers[0], BuildProjectBuildWrapper)

        if builds_are_build_step:
            for build_wrapper in build_wrappers:
                # Update the 'report' object with info about how many lines to print for each build.
                # This information is only available after the build has finished.
                report.set_report_length(
                    name=build_wrapper.name,
                    report_length_lines=build_wrapper.report_length_lines,
                )

        # If all are OK then we should print the resource utilization numbers.
        # If not, then we print a few last lines of the log output.
        if builds_are_build_step or not all_builds_ok:
            report.print_str()

        return all_builds_ok


class BuildProjectWrapper(ABC):
    """
    Mimics a VUnit test case object.
    """

    def get_seed(self) -> str:
        """
        Required since VUnit version 5.0.0.dev6, where a 'get_seed' method was added
        to the 'TestSuiteWrapper' class, which calls a 'get_seed' method expected to be implemented
        in the test case object.
        This mechanism is not used by tsfpga, but is required in order to avoid errors.
        Adding a dummy implementation like this makes sure it works with older as well as newer
        versions of VUnit.
        """
        return ""

    @abstractmethod
    def run(
        self,
        output_path: Path,
        read_output: Any,  # noqa: ANN401
    ) -> bool:
        pass


class BuildProjectCreateWrapper(BuildProjectWrapper):
    """
    Wrapper to create a build project, for usage in the build runner.
    """

    def __init__(
        self,
        project: VivadoProject,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        self.name = project.name
        self._project = project
        self._create_arguments = kwargs

    def run(
        self,
        output_path: Path,
        read_output: Any,  # noqa: ANN401, ARG002
    ) -> bool:
        """
        Argument 'read_output' sent by VUnit test runner is unused by us.
        """
        this_project_path = Path(output_path) / "project"
        return self._project.create(project_path=this_project_path, **self._create_arguments)


class BuildProjectBuildWrapper(BuildProjectWrapper):
    """
    Wrapper to build a project, for usage in the build runner.
    """

    def __init__(
        self,
        project: VivadoProject,
        collect_artifacts: Callable[..., bool] | None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        self.name = project.name
        self._project = project
        self._collect_artifacts = collect_artifacts
        self._build_arguments = kwargs

        self._report_length_lines: int | None = None

    def run(
        self,
        output_path: Path,
        read_output: Any,  # noqa: ANN401, ARG002
    ) -> bool:
        """
        Argument 'read_output' sent by VUnit test runner is unused by us.
        """
        this_project_path = Path(output_path) / "project"
        build_result = self._project.build(project_path=this_project_path, **self._build_arguments)

        if not build_result.success:
            self._print_build_result(build_result=build_result)
            return build_result.success

        # Proceed to artifact collection only if build succeeded.
        if self._collect_artifacts is not None:
            build_result.success &= self._collect_artifacts(
                project=self._project, output_path=self._build_arguments["output_path"]
            )

        # Print size at the absolute end.
        self._print_build_result(build_result=build_result)
        return build_result.success

    def _print_build_result(self, build_result: build_result.BuildResult) -> None:
        build_report = build_result.report()

        if build_report:
            print(build_report)
            self._report_length_lines = build_report.count("\n") + 1

    @property
    def report_length_lines(self) -> int | None:
        """
        The number of lines in the ``build_result`` report from this project.
        A value of ``None`` would indicate a build failure, either in the IDE or in the
        post-build steps.
        """
        return self._report_length_lines


class BuildProjectOpenWrapper(BuildProjectWrapper):
    """
    Wrapper to open a build project, for usage in the build runner.
    """

    def __init__(self, project: VivadoProject) -> None:
        self.name = project.name
        self._project = project

    def run(
        self,
        output_path: Path,
        read_output: Any,  # noqa: ANN401, ARG002
    ) -> bool:
        """
        Argument 'read_output' sent by VUnit test runner is unused by us.
        """
        this_project_path = Path(output_path) / "project"
        return self._project.open(project_path=this_project_path)


class BuildRunner(TestRunner):
    """
    Build runner that mimics a VUnit TestRunner. Most things are used as they are in the
    base class, but some behavior is overridden.
    """

    def _create_test_mapping_file(
        self,
        test_suites: Any,  # noqa: ANN401
    ) -> None:
        """
        Overloaded from super class.

        Do not create this file.

        We do not need it since folder name is the same as project name.
        """

    def _get_output_path(self, test_suite_name: str) -> str:
        """
        Overloaded from super class.

        Output folder name is the same as the project name.

        Original function adds a hash at the end of the folder name.
        We do not want that necessarily.
        """
        return str(Path(self._output_path) / test_suite_name)

    @staticmethod
    def _prepare_test_suite_output_path(output_path: str) -> None:
        """
        Overloaded from super class.

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

    def __init__(self, collect_artifacts: Callable[[VivadoProject, Path], bool]) -> None:
        self._collect_artifacts = collect_artifacts
        self._lock = Lock()

    def collect_artifacts(self, project: VivadoProject, output_path: Path) -> bool:
        with self._lock:
            return self._collect_artifacts(project=project, output_path=output_path)


class BuildReport(TestReport):
    def add_result(
        self,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """
        Overloaded from super class.

        Add a a test result.

        Uses a different Result class than the super method.
        """
        result = BuildResult(*args, **kwargs)
        self._test_results[result.name] = result
        self._test_names_in_order.append(result.name)

    def set_report_length(self, name: str, report_length_lines: int | None) -> None:
        """
        Set how many lines shall be printed for this build.
        Can be ``None`` to indicate that the build failed, and we don't how much to print.
        """
        self._test_results[name].set_report_length(report_length_lines=report_length_lines)

    def print_latest_status(self, total_tests: int) -> None:
        """
        Overloaded from super class.

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
            raise AssertionError

        count_summary = f"pass={len(passed)} fail={len(failed)} total={total_tests}"
        self._printer.write(f" ({count_summary}) {result.name} ({result.time:.1f} seconds)\n")


class BuildResult(TestResult):
    _report_length_lines: int | None = None

    def _print_output(
        self,
        printer: ColorPrinter,
        num_lines: int,
    ) -> None:
        """
        Print the last lines from the output file.
        """
        output_tail = read_last_lines_of_file(Path(self._output_file_name), num_lines=num_lines)
        printer.write(output_tail)

    def set_report_length(self, report_length_lines: int) -> None:
        """
        Set how many lines shall be printed when this result is printed.
        Can be ``None`` to indicate that the build failed, and we don't how much to print.
        """
        self._report_length_lines = report_length_lines

    def print_status(
        self,
        printer: ColorPrinter,
        padding: int = 0,
        **kwargs: dict[str, Any],
    ) -> None:
        """
        Overloaded from super class.

        This method is called for each build when it should print its result in the "Summary" at
        the end when all builds have finished.

        Inherited and adapted from the VUnit function.

        Note that a ``max_time`` integer argument is added in VUnit >4.7.0, but at the time of
        writing this is un-released on the VUnit ``master`` branch.
        In order to be compatible with both older and newer versions, we use ``**kwargs`` for this.
        """
        if self.passed and self._report_length_lines is not None:
            # Build passed, print build summary of the specified length. The length is only
            # set if this is a "build" result (not "create" or "open").
            self._print_output(printer=printer, num_lines=self._report_length_lines)

        else:
            # The build failed, which can either be caused by
            # 1. IDE build failure
            # 2. IDE build succeeded, but post build hook, or size checkers failed.
            # 3. Other python error (directory already exists, ...)
            # In the case of IDE build failed, we want a significant portion of the output, to be
            # able to see an indication of what failed.
            # In the case of size checkers, we want to see all the printouts from all checkers,
            # to see which one failed.
            self._print_output(printer=printer, num_lines=25)

        # Print the regular output from the VUnit class.
        # A little extra margin between build name and execution time makes the output more readable
        super().print_status(printer=printer, padding=padding + 2, **kwargs)
        # Add an empty line between each build, for readability.
        printer.write("\n")


def get_build_projects(
    modules: ModuleList, project_filters: list[str], include_netlist_not_full_builds: bool = False
) -> list[VivadoProject]:
    """
    Get build projects from the given modules that match the given filters.
    Note that the result of this function is a list of "raw" :class:`.VivadoProject` objects.
    These are meant to be passed to :class:`.BuildProjectList` for execution.

    Arguments:
        modules: Module objects that can define build projects.
        project_filters: Project name filters.
            Can use wildcards (*).
            Leave empty for all.
        include_netlist_not_full_builds:
            Set True to get only netlist builds, instead of only full top level builds.
    """
    result = []
    for module in modules:
        for project in module.get_build_projects():
            if project.is_netlist_build == include_netlist_not_full_builds:
                if not project_filters:
                    result.append(project)

                else:
                    for project_filter in project_filters:
                        if fnmatch.filter([project.name], project_filter):
                            result.append(project)

                            # Do not continue with further filters if we have already matched
                            # this project.
                            # Multiple filters might match the same project, and we dont't
                            # want duplicates.
                            break

    return result
