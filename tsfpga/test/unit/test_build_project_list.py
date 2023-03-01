# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import unittest
from unittest.mock import MagicMock

# Third party libraries
import pytest

# First party libraries
from tsfpga.build_project_list import BuildProjectList
from tsfpga.module import BaseModule
from tsfpga.system_utils import create_directory
from tsfpga.vivado.project import BuildResult, VivadoProject


# pylint: disable=too-many-instance-attributes
@pytest.mark.usefixtures("fixture_tmp_path")
class TestBuildProjectList(unittest.TestCase):
    tmp_path = None

    @staticmethod
    def _get_mocks(name, is_netlist_build):
        project = MagicMock(spec=VivadoProject)
        project.name = name
        project.__str__.return_value = f"MockProject {name}"
        project.is_netlist_build = is_netlist_build

        module = MagicMock(spec=BaseModule)
        module.name = name
        module.get_build_projects.return_value = [project]

        return module, project

    def setUp(self):
        self.module_one, self.project_one = self._get_mocks("one", False)
        self.module_two, self.project_two = self._get_mocks("two", False)

        self.module_three, self.project_three = self._get_mocks("three", True)
        self.module_four, self.project_four = self._get_mocks("four", True)

        self.modules = [self.module_one, self.module_two, self.module_three, self.module_four]

    def test_can_list_without_error(self):
        list_str = str(BuildProjectList(self.modules))
        assert "one" in list_str
        assert "two" in list_str

    def test_project_filtering(self):
        project_list = BuildProjectList(self.modules)
        assert len(project_list.projects) == 2
        assert self.project_one in project_list.projects
        assert self.project_two in project_list.projects

        project_list = BuildProjectList(
            self.modules, project_filters=["apa", "*ne", "three", "four"]
        )
        assert len(project_list.projects) == 1
        assert self.project_one in project_list.projects

        project_list = BuildProjectList(self.modules, project_filters=["one", "one", "on*"])
        assert len(project_list.projects) == 1
        assert self.project_one in project_list.projects

        project_list = BuildProjectList(self.modules, include_netlist_not_top_builds=True)
        assert len(project_list.projects) == 2
        assert self.project_three in project_list.projects
        assert self.project_four in project_list.projects

        project_list = BuildProjectList(
            self.modules,
            include_netlist_not_top_builds=True,
            project_filters=["apa", "one", "two", "thr*"],
        )
        assert len(project_list.projects) == 1
        assert self.project_three in project_list.projects

    def test_create(self):
        project_list = BuildProjectList(self.modules, project_filters=["one", "two"])
        assert project_list.create(
            projects_path=self.tmp_path / "projects_path",
            num_parallel_builds=2,
            ip_cache_path=self.tmp_path / "ip_cache_path",
        )

        self.project_one.create.assert_called_once_with(
            project_path=self.tmp_path / "projects_path" / "one" / "project",
            ip_cache_path=self.tmp_path / "ip_cache_path",
        )

        self.project_two.create.assert_called_once_with(
            project_path=self.tmp_path / "projects_path" / "two" / "project",
            ip_cache_path=self.tmp_path / "ip_cache_path",
        )

        self.project_three.create.assert_not_called()
        self.project_four.create.assert_not_called()

    def test_create_unless_exists(self):
        project_list = BuildProjectList(self.modules, project_filters=["one"])
        assert project_list.create_unless_exists(
            projects_path=self.tmp_path / "projects_path",
            num_parallel_builds=2,
            ip_cache_path=self.tmp_path / "ip_cache_path",
        )

        self.project_one.create.assert_called_once_with(
            project_path=self.tmp_path / "projects_path" / "one" / "project",
            ip_cache_path=self.tmp_path / "ip_cache_path",
        )

        # Create project file manually
        create_directory(self.tmp_path / "projects_path" / "one" / "project")
        (self.tmp_path / "projects_path" / "one" / "project" / "one.xpr").write_text("")

        assert project_list.create_unless_exists(
            projects_path=self.tmp_path / "projects_path",
            num_parallel_builds=2,
            ip_cache_path=self.tmp_path / "ip_cache_path",
        )

        # Still only called once after second create_unless_exists()
        self.project_one.create.assert_called_once()

        self.project_two.create.assert_not_called()
        self.project_three.create.assert_not_called()
        self.project_four.create.assert_not_called()

    def test_build(self):
        project_list = BuildProjectList(self.modules, project_filters=["one"])
        assert project_list.build(
            projects_path=self.tmp_path / "projects_path",
            num_parallel_builds=2,
            num_threads_per_build=4,
            other_build_argument=True,
        )

        self.project_one.build.assert_called_once_with(
            project_path=self.tmp_path / "projects_path" / "one" / "project",
            output_path=self.tmp_path / "projects_path" / "one",
            num_threads=4,
            other_build_argument=True,
        )

    def test_build_fail_should_return_false(self):
        project_list = BuildProjectList(self.modules, project_filters=["one"])
        self.project_one.build.return_value = MagicMock(spec=BuildResult)
        self.project_one.build.return_value.success = False

        assert not project_list.build(
            projects_path=self.tmp_path / "projects_path",
            num_parallel_builds=2,
            num_threads_per_build=4,
            other_build_argument=True,
        )

    def test_build_with_output_path(self):
        project_list = BuildProjectList(self.modules, project_filters=["one"])
        assert project_list.build(
            projects_path=self.tmp_path / "projects_path",
            num_parallel_builds=2,
            num_threads_per_build=4,
            output_path=self.tmp_path / "output_path",
        )

        self.project_one.build.assert_called_once_with(
            project_path=self.tmp_path / "projects_path" / "one" / "project",
            output_path=self.tmp_path / "output_path" / "one",
            num_threads=4,
        )

    def test_build_with_collect_artifacts(self):
        project_list = BuildProjectList(self.modules, project_filters=["one"])
        collect_artifacts = MagicMock()
        assert project_list.build(
            projects_path=self.tmp_path / "projects_path",
            num_parallel_builds=2,
            num_threads_per_build=4,
            collect_artifacts=collect_artifacts,
        )

        collect_artifacts.assert_called_once_with(
            project=self.project_one,
            output_path=self.tmp_path / "projects_path" / "one",
        )

    def test_build_with_collect_artifacts_and_output_path(self):
        project_list = BuildProjectList(self.modules, project_filters=["one"])
        collect_artifacts = MagicMock()
        assert project_list.build(
            projects_path=self.tmp_path / "projects_path",
            num_parallel_builds=2,
            num_threads_per_build=4,
            output_path=self.tmp_path / "output_path",
            collect_artifacts=collect_artifacts,
        )

        collect_artifacts.assert_called_once_with(
            project=self.project_one, output_path=self.tmp_path / "output_path" / "one"
        )

    def test_build_with_collect_artifacts_return_false_should_fail_build(self):
        project_list = BuildProjectList(self.modules, project_filters=["one"])
        collect_artifacts = MagicMock()
        collect_artifacts.return_value = False
        assert not project_list.build(
            projects_path=self.tmp_path / "projects_path",
            num_parallel_builds=2,
            num_threads_per_build=4,
            collect_artifacts=collect_artifacts,
        )

    def test_open(self):
        project_list = BuildProjectList(self.modules, include_netlist_not_top_builds=True)
        assert project_list.open(projects_path=self.tmp_path / "projects_path")

        self.project_three.open.assert_called_once_with(
            project_path=self.tmp_path / "projects_path" / "three" / "project"
        )
        self.project_four.open.assert_called_once_with(
            project_path=self.tmp_path / "projects_path" / "four" / "project"
        )
        self.project_one.open.assert_not_called()
        self.project_two.open.assert_not_called()
