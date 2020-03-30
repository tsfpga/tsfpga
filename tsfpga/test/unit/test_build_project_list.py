# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import unittest

import pytest

from tsfpga.build_project_list import BuildProjectList


class TestBuildProjectList(unittest.TestCase):

    def setUp(self):
        modules = [DummyModule("a"), DummyModule("b")]
        self.projects = BuildProjectList(modules)

        assert len(self.projects.names()) == 2

    def test_get_project(self):
        assert self.projects.get("a").name == "a"
        assert self.projects.get("b").name == "b"

    def test_get_project_with_name_that_does_not_exist_shall_raise_exception(self):
        with pytest.raises(ValueError) as exception_info:
            self.projects.get("c")
        assert str(exception_info.value) == "Could not find project: c"

    def test_can_cast_to_string_without_error(self):
        str(self.projects)


class DummyModule:

    def __init__(self, name):
        self.name = name

    def get_build_projects(self):
        return [DummyBuildProject(self.name)]


class DummyBuildProject:

    def __init__(self, name):
        self.name = name
