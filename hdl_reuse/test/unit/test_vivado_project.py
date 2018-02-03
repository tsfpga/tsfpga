from os.path import dirname, join
import pytest
import unittest

from hdl_reuse.module import get_modules
from hdl_reuse.test import create_file, create_directory, delete
from hdl_reuse.vivado_project import VivadoProject


THIS_DIR = dirname(__file__)

# pylint: disable=protected-access


class TestBasicProject(unittest.TestCase):

    part = "xczu3eg-sfva625-1-i"
    project_folder = join(THIS_DIR, "vivado")
    modules_folder = join(THIS_DIR, "modules")

    def setUp(self):
        # A library with some synth files and some test files
        self.a_vhd = create_file(join(self.modules_folder, "apa", "a.vhd"))
        self.tb_a_vhd = create_file(join(self.modules_folder, "apa", "test", "tb_a.vhd"))
        self.b_vhd = create_file(join(self.modules_folder, "apa", "b.vhd"))
        self.b_tcl = create_file(join(self.modules_folder, "apa", "entity_constraints", "b.tcl"))

        # A library with only test files
        self.c_vhd = create_file(join(self.modules_folder, "zebra", "test", "c.vhd"))

        self.modules = get_modules([self.modules_folder])
        self.proj = VivadoProject(name="name", modules=self.modules, part=self.part)

    def tearDown(self):
        delete(self.modules_folder)
        delete(self.project_folder)

    def test_constraints(self):
        b_tcl_found = False
        for constraint in self.proj.constraints:
            if constraint.file == self.b_tcl:
                b_tcl_found = True
                assert constraint.ref == "b"
                assert constraint.used_in == "all"
        assert b_tcl_found

    def test_only_synthesis_files_added_to_create_project_tcl(self):
        tcl = self.proj._create_tcl(self.project_folder)
        assert self.a_vhd in tcl and self.b_vhd in tcl
        assert self.tb_a_vhd not in tcl and "tb_a.vhd" not in tcl

    def test_empty_library_not_in_create_project_tcl(self):
        tcl = self.proj._create_tcl(self.project_folder)
        assert "zebra" not in tcl

    def test_create_should_raise_exeception_if_project_path_already_exists(self):
        create_directory(self.project_folder)
        with pytest.raises(ValueError):
            self.proj.create(self.project_folder)

    def test_build_should_raise_exeception_if_project_does_not_exists(self):
        with pytest.raises(ValueError):
            self.proj.build(self.project_folder)

    def test_build_with_impl_run_should_raise_exeception_if_no_output_path_is_given(self):
        with pytest.raises(ValueError):
            self.proj.build(self.project_folder)
