from os.path import dirname, join
import unittest

from hdl_reuse.module import get_modules
from hdl_reuse.test import create_file, delete
from hdl_reuse.vivado_tcl import VivadoTcl


THIS_DIR = dirname(__file__)


class TestVivadoTcl(unittest.TestCase):

    modules_folder = join(THIS_DIR, "modules")

    def setUp(self):
        delete(self.modules_folder)

        # A library with some synth files and some test files
        self.a_vhd = create_file(join(self.modules_folder, "apa", "a.vhd"))
        self.tb_a_vhd = create_file(join(self.modules_folder, "apa", "test", "tb_a.vhd"))
        self.b_vhd = create_file(join(self.modules_folder, "apa", "b.vhd"))
        self.b_tcl = create_file(join(self.modules_folder, "apa", "entity_constraints", "b.tcl"))

        # A library with only test files
        self.c_vhd = create_file(join(self.modules_folder, "zebra", "test", "c.vhd"))

        self.modules = get_modules([self.modules_folder])
        self.tcl = VivadoTcl(name="name", modules=self.modules, part="part", top="top", constraints=[])

    def test_only_synthesis_files_added_to_create_project_tcl(self):
        tcl = self.tcl.create(project_folder="")
        assert self.a_vhd in tcl and self.b_vhd in tcl
        assert self.tb_a_vhd not in tcl and "tb_a.vhd" not in tcl

    def test_empty_library_not_in_create_project_tcl(self):
        tcl = self.tcl.create(project_folder="")
        assert "zebra" not in tcl
