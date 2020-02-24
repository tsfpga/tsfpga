# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import unittest

import pytest

from tsfpga.system_utils import create_file, create_directory
from tsfpga.fpga_project_list import FpgaProjectList


@pytest.mark.usefixtures("fixture_tmp_path")
class TestFpgaProjectList(unittest.TestCase):

    tmp_path = None

    def setUp(self):
        module_file_content = """
class Dummy:

    def __init__(self):
        self.name = \"{name}\"

def get_projects():
    return [Dummy()]
"""

        create_file(self.tmp_path / "a" / "project_a.py", module_file_content.format(name="a"))
        create_file(self.tmp_path / "b" / "project_b.py", module_file_content.format(name="b"))

        create_directory(self.tmp_path / "c")

        self.projects = FpgaProjectList([self.tmp_path])
        assert len(self.projects.names()) == 2

    def test_get_project(self):
        assert self.projects.get("a").name == "a"
        assert self.projects.get("b").name == "b"

    def test_get_project_with_name_that_does_not_exist(self):
        with pytest.raises(ValueError) as exception_info:
            self.projects.get("c")
        assert str(exception_info.value) == "Could not find project: c"
