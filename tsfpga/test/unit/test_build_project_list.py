# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import unittest

import pytest

from tsfpga.build_project_list import BuildProjectList


class TestBuildProjectList(unittest.TestCase):

    def setUp(self):
        modules = [DummyModule("one"), DummyModule("two")]
        modules += [DummyNetlistModule("three"), DummyNetlistModule("four"), DummyNetlistModule("five")]
        self.projects = BuildProjectList(modules)

    def test_get_project(self):
        projects = self.projects.get_projects(["one"], False)
        assert len(projects) == 1
        expected = {"one"}
        assert {project.name for project in projects} == expected

        projects = self.projects.get_projects(["*o*"], False)
        assert len(projects) == 2
        expected = {"one", "two"}
        assert {project.name for project in projects} == expected

        projects = self.projects.get_projects(["*o*"], True)
        assert len(projects) == 1
        expected = {"four"}
        assert {project.name for project in projects} == expected

        projects = self.projects.get_projects(["*e*"], True)
        assert len(projects) == 2
        expected = {"three", "five"}
        assert {project.name for project in projects} == expected

        projects = self.projects.get_projects(["four", "*e*"], True)
        assert len(projects) == 3
        expected = {"three", "four", "five"}
        assert {project.name for project in projects} == expected

    def test_get_project_with_name_that_does_not_exist_shall_raise_exception(self):
        with pytest.raises(ValueError) as exception_info:
            self.projects.get_projects(["f"], False)
        assert str(exception_info.value) == "Could not find projects with filters: ['f']"
        with pytest.raises(ValueError) as exception_info:
            self.projects.get_projects(["one"], True)
        assert str(exception_info.value) == "Could not find projects with filters: ['one']"
        with pytest.raises(ValueError) as exception_info:
            self.projects.get_projects(["three"], False)
        assert str(exception_info.value) == "Could not find projects with filters: ['three']"

    def test_can_cast_to_string_without_error(self):
        str(self.projects)


class DummyModule:

    def __init__(self, name):
        self.name = name

    def get_build_projects(self):
        return [DummyBuildProject(self.name, False)]


class DummyNetlistModule:

    def __init__(self, name):
        self.name = name

    def get_build_projects(self):
        return [DummyBuildProject(self.name, True)]


class DummyBuildProject:

    def __init__(self, name, is_netlist_build):
        self.name = name
        self.is_netlist_build = is_netlist_build
