# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from unittest.mock import MagicMock

import pytest

from tsfpga.build_project_list import BuildProjectList, get_build_projects
from tsfpga.module import BaseModule
from tsfpga.system_utils import create_directory
from tsfpga.vivado.project import BuildResult, VivadoProject


@pytest.fixture
def build_project_list_test():
    class TestBuildProjectList:
        @staticmethod
        def _get_mocks(name, is_netlist_build=False):
            project = MagicMock(spec=VivadoProject)
            project.name = name
            project.__str__.return_value = f"MockProject {name}"
            project.is_netlist_build = is_netlist_build

            # Note that his has 'success' set to True by default.
            project.build.return_value = BuildResult(name=name, synthesis_run_name="")

            module = MagicMock(spec=BaseModule)
            module.name = name
            module.get_build_projects.return_value = [project]

            return module, project

        def __init__(self):
            self.module_one, self.project_one = self._get_mocks(name="one")
            self.module_two, self.project_two = self._get_mocks(name="two")

            self.module_three, self.project_three = self._get_mocks(
                name="three", is_netlist_build=True
            )
            self.module_four, self.project_four = self._get_mocks(
                name="four", is_netlist_build=True
            )

            self.modules = [self.module_one, self.module_two, self.module_three, self.module_four]
            self.projects = [
                self.project_one,
                self.project_two,
                self.project_three,
                self.project_four,
            ]

    return TestBuildProjectList()


def test_get_build_projects(build_project_list_test):
    assert get_build_projects(
        modules=build_project_list_test.modules,
        project_filters=[],
        include_netlist_not_full_builds=True,
    ) == [
        build_project_list_test.project_three,
        build_project_list_test.project_four,
    ]
    assert get_build_projects(
        modules=build_project_list_test.modules,
        project_filters=[],
        include_netlist_not_full_builds=False,
    ) == [
        build_project_list_test.project_one,
        build_project_list_test.project_two,
    ]

    assert get_build_projects(
        modules=build_project_list_test.modules,
        project_filters=["thr*", "fou*"],
        include_netlist_not_full_builds=True,
    ) == [
        build_project_list_test.project_three,
        build_project_list_test.project_four,
    ]

    # Filter matches 'three' twice, but should only return once.
    assert get_build_projects(
        modules=build_project_list_test.modules,
        project_filters=["three", "*r*"],
        include_netlist_not_full_builds=True,
    ) == [
        build_project_list_test.project_three,
        build_project_list_test.project_four,
    ]


def test_can_list_without_error(build_project_list_test):
    list_str = str(BuildProjectList(build_project_list_test.projects))
    assert "one" in list_str
    assert "two" in list_str


def test_create(build_project_list_test, tmp_path):
    project_list = BuildProjectList(build_project_list_test.projects)
    assert project_list.create(
        projects_path=tmp_path / "projects_path",
        num_parallel_builds=2,
        ip_cache_path=tmp_path / "ip_cache_path",
    )

    for project in build_project_list_test.projects:
        project.create.assert_called_once_with(
            project_path=tmp_path / "projects_path" / project.name / "project",
            ip_cache_path=tmp_path / "ip_cache_path",
        )


def test_create_unless_exists(build_project_list_test, tmp_path):
    project_list = BuildProjectList([build_project_list_test.project_one])
    assert project_list.create_unless_exists(
        projects_path=tmp_path / "projects_path",
        num_parallel_builds=2,
        ip_cache_path=tmp_path / "ip_cache_path",
    )

    build_project_list_test.project_one.create.assert_called_once_with(
        project_path=tmp_path / "projects_path" / "one" / "project",
        ip_cache_path=tmp_path / "ip_cache_path",
    )

    # Create project file manually
    create_directory(tmp_path / "projects_path" / "one" / "project")
    (tmp_path / "projects_path" / "one" / "project" / "one.xpr").write_text("")

    assert project_list.create_unless_exists(
        projects_path=tmp_path / "projects_path",
        num_parallel_builds=2,
        ip_cache_path=tmp_path / "ip_cache_path",
    )

    # Still only called once after second create_unless_exists()
    build_project_list_test.project_one.create.assert_called_once()


def test_build(build_project_list_test, tmp_path):
    project_list = BuildProjectList([build_project_list_test.project_one])
    assert project_list.build(
        projects_path=tmp_path / "projects_path",
        num_parallel_builds=2,
        num_threads_per_build=4,
        other_build_argument=True,
    )

    build_project_list_test.project_one.build.assert_called_once_with(
        project_path=tmp_path / "projects_path" / "one" / "project",
        output_path=tmp_path / "projects_path" / "one",
        num_threads=4,
        other_build_argument=True,
    )


def test_build_fail_should_return_false(build_project_list_test, tmp_path):
    project_list = BuildProjectList([build_project_list_test.project_one])
    build_project_list_test.project_one.build.return_value = MagicMock(spec=BuildResult)
    build_project_list_test.project_one.build.return_value.success = False

    assert not project_list.build(
        projects_path=tmp_path / "projects_path",
        num_parallel_builds=2,
        num_threads_per_build=4,
        other_build_argument=True,
    )


def test_build_with_output_path(build_project_list_test, tmp_path):
    project_list = BuildProjectList([build_project_list_test.project_one])
    assert project_list.build(
        projects_path=tmp_path / "projects_path",
        num_parallel_builds=2,
        num_threads_per_build=4,
        output_path=tmp_path / "output_path",
    )

    build_project_list_test.project_one.build.assert_called_once_with(
        project_path=tmp_path / "projects_path" / "one" / "project",
        output_path=tmp_path / "output_path" / "one",
        num_threads=4,
    )


def test_build_with_collect_artifacts(build_project_list_test, tmp_path):
    project_list = BuildProjectList([build_project_list_test.project_one])
    collect_artifacts = MagicMock()
    assert project_list.build(
        projects_path=tmp_path / "projects_path",
        num_parallel_builds=2,
        num_threads_per_build=4,
        collect_artifacts=collect_artifacts,
    )

    collect_artifacts.assert_called_once_with(
        project=build_project_list_test.project_one,
        output_path=tmp_path / "projects_path" / "one",
    )


def test_build_with_collect_artifacts_and_output_path(build_project_list_test, tmp_path):
    project_list = BuildProjectList([build_project_list_test.project_one])
    collect_artifacts = MagicMock()
    assert project_list.build(
        projects_path=tmp_path / "projects_path",
        num_parallel_builds=2,
        num_threads_per_build=4,
        output_path=tmp_path / "output_path",
        collect_artifacts=collect_artifacts,
    )

    collect_artifacts.assert_called_once_with(
        project=build_project_list_test.project_one,
        output_path=tmp_path / "output_path" / "one",
    )


def test_build_with_collect_artifacts_return_false_should_fail_build(
    build_project_list_test, tmp_path
):
    project_list = BuildProjectList([build_project_list_test.project_one])
    collect_artifacts = MagicMock()
    collect_artifacts.return_value = False
    assert not project_list.build(
        projects_path=tmp_path / "projects_path",
        num_parallel_builds=2,
        num_threads_per_build=4,
        collect_artifacts=collect_artifacts,
    )


def test_open(build_project_list_test, tmp_path):
    project_list = BuildProjectList(
        [build_project_list_test.project_three, build_project_list_test.project_four]
    )
    assert project_list.open(projects_path=tmp_path / "projects_path")

    build_project_list_test.project_three.open.assert_called_once_with(
        project_path=tmp_path / "projects_path" / "three" / "project"
    )
    build_project_list_test.project_four.open.assert_called_once_with(
        project_path=tmp_path / "projects_path" / "four" / "project"
    )
    build_project_list_test.project_one.open.assert_not_called()
    build_project_list_test.project_two.open.assert_not_called()
