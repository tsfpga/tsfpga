from os.path import dirname, join
import pytest
import unittest

from hdl_reuse.module import get_modules
from hdl_reuse.test import create_file, create_directory, delete
from hdl_reuse.vivado_project import VivadoProject


THIS_DIR = dirname(__file__)


class TestBasicProject(unittest.TestCase):

    project_folder = join(THIS_DIR, "vivado")
    modules_folder = join(THIS_DIR, "modules")

    def setUp(self):
        delete(self.modules_folder)
        delete(self.project_folder)

        self.b_vhd = create_file(join(self.modules_folder, "apa", "b.vhd"))
        self.b_tcl = create_file(join(self.modules_folder, "apa", "entity_constraints", "b.tcl"))

        self.modules = get_modules([self.modules_folder])
        self.proj = VivadoProject(name="name", modules=self.modules, part="part")

    def test_constraints(self):
        b_tcl_found = False
        for constraint in self.proj._setup_constraints_list([]):  # pylint: disable=protected-access
            if constraint.file == self.b_tcl:
                b_tcl_found = True
                assert constraint.ref == "b"
                assert constraint.used_in == "all"
        assert b_tcl_found

    def test_create_should_raise_exception_if_project_path_already_exists(self):
        create_directory(self.project_folder)
        with pytest.raises(ValueError) as exception_info:
            self.proj.create(self.project_folder)
        assert str(exception_info.value).startswith("Folder already exists")

    def test_build_should_raise_exception_if_project_does_not_exists(self):
        with pytest.raises(ValueError) as exception_info:
            self.proj.build(self.project_folder, synth_only=True)
        assert str(exception_info.value).startswith("Project file does not exist")

    def test_build_with_impl_run_should_raise_exception_if_no_output_path_is_given(self):
        with pytest.raises(ValueError) as exception_info:
            self.proj.build(self.project_folder)
        assert str(exception_info.value).startswith("Must specify output_path")
