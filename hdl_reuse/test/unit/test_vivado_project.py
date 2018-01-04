from os import makedirs
from os.path import dirname, join, exists
import pytest
from shutil import rmtree
import unittest

from hdl_reuse.module import get_modules
from hdl_reuse.test.test_utils import create_file
from hdl_reuse.vivado_project import VivadoProject


THIS_DIR = dirname(__file__)

# pylint: disable=protected-access


class TestBasicProject(unittest.TestCase):

    part = "xczu3eg-sfva625-1-i"
    project_folder = join(THIS_DIR, "vivado")
    modules_folder = join(THIS_DIR, "modules")

    def setUp(self):
        # A library with some synth files and some test files
        self.file_a = create_file(join(self.modules_folder, "apa", "a.vhd"))
        self.file_b = create_file(join(self.modules_folder, "apa", "b.vhd"))
        self.file_c = create_file(join(self.modules_folder, "apa", "test", "c.vhd"))

        # A library with only test files
        makedirs(join(self.modules_folder, "zebra", "test"))
        self.file_d = create_file(join(self.modules_folder, "zebra", "test", "d.vhd"))

        self.modules = get_modules([self.modules_folder])
        self.proj = VivadoProject(name="name", modules=self.modules, part=self.part, vivado_path="")

    def tearDown(self):
        rmtree(self.modules_folder)
        if exists(self.project_folder):
            rmtree(self.project_folder)

    def test_only_synthesis_files_added_to_create_project_tcl(self):
        tcl = self.proj._create_tcl(self.project_folder)
        assert self.file_a in tcl and self.file_b in tcl
        assert self.file_c not in tcl and "c.vhd" not in tcl

    def test_empty_library_not_in_create_project_tcl(self):
        tcl = self.proj._create_tcl(self.project_folder)
        assert "zebra" not in tcl

    def test_should_raise_exeception_if_project_path_already_exists(self):
        makedirs(self.project_folder)
        with pytest.raises(ValueError):
            self.proj.create(self.project_folder)
