# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import dirname, join
import unittest

from tsfpga.system_utils import create_file, create_directory, delete
from tsfpga.fpga_project_list import FPGAProjectList


THIS_DIR = dirname(__file__)


class TestFPGAProjectList(unittest.TestCase):

    _modules_folder = join(THIS_DIR, "modules_for_test")
    _modules_folders = [_modules_folder]

    def setUp(self):
        delete(self._modules_folder)
        create_directory(join(self._modules_folder, "a"))
        create_directory(join(self._modules_folder, "b"))
        create_directory(join(self._modules_folder, "c"))

    def test_get_projects(self):
        module_file_content = """
class Dummy:

    def __init__(self):
        self.name = \"{name}\"

def get_projects():
    return [Dummy()]
"""

        create_file(join(self._modules_folder, "a", "project_a.py"), module_file_content.format(name="a"))
        create_file(join(self._modules_folder, "b", "project_b.py"), module_file_content.format(name="b"))

        projects = FPGAProjectList(self._modules_folders)

        assert len(projects.names()) == 2
        assert projects.get("a").name == "a"
        assert projects.get("b").name == "b"
