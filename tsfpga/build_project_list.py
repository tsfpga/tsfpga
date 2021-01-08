# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import fnmatch
from pathlib import Path
from threading import Lock

from vunit.test.list import TestList
from vunit.test.runner import TestRunner
from vunit.test.report import TestReport
from vunit.color_printer import COLOR_PRINTER, NO_COLOR_PRINTER

from tsfpga.system_utils import create_directory


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
            modules (list(:class:`.BaseModule`)): Module objects that can define build
                projects.
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

    def __str__(self):
        """
        Returns a string with a description list of the projects.
        """
        return "\n\n".join([str(project) for project in self.projects])

    def create(self, projects_path, num_parallel_builds, **kwargs):
        """
        Create build project on disk for all the projects in the list.

        Arguments:
            projects_path (`pathlib.Path`): The projects will be placed here.
            num_parallel_builds (int): The number of projects that will be created in
                parallel.
            kwargs: Other arguments as accpeted by :meth:`.VivadoProject.create`.

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
            projects_path (`pathlib.Path`): The projects will be placed here.
            num_parallel_builds (int): The number of projects that will be created in
                parallel.
            kwargs: Other arguments as accpeted by :meth:`.VivadoProject.create`.

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
        **kwargs
    ):
        """
        Build all the projects in the list.

        Arguments:
            projects_path (`pathlib.Path`): The projects will be placed here.
            num_parallel_builds (int): The number of projects that will be built in
                parallel.
            num_threads_per_build (int): The number threads that will be used for each
                parallel build process.
            output_path (`pathlib.Path`): Where the artifacts should be placed.
            collect_artifacts (`function`): Callback to collect artifacts. Takes two named
                arguments:

                |  **project** (:class:`.VivadoProject`): The project that is being built.

                |  **output_path** (`pathlib.Path`): Where the artifacts should be placed.


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
                **kwargs
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
            projects_path (`pathlib.Path`): The projects are placed here.

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
        verbosity = BuildRunner.VERBOSITY_QUIET

        color_printer = NO_COLOR_PRINTER if self._no_color else COLOR_PRINTER
        report = TestReport(printer=color_printer)

        test_list = TestList()
        for build_wrapper in build_wrappers:
            test_list.add_test(build_wrapper)

        test_runner = BuildRunner(
            report=report,
            output_path=projects_path,
            verbosity=verbosity,
            num_threads=num_parallel_builds,
        )
        test_runner.run(test_list)

        return report.all_ok()

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
            return build_result.success

        if self._collect_artifacts is not None:
            if not self._collect_artifacts(
                project=self._project, output_path=self._build_arguments["output_path"]
            ):
                build_result.success = False

        return build_result.success


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
