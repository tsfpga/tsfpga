from os.path import dirname, join, abspath
import unittest
from collections import OrderedDict

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
        self.a_xdc = create_file(join(self.modules_folder, "apa", "scoped_constraints", "a.xdc"))

        self.b_vhd = create_file(join(self.modules_folder, "apa", "b.vhd"))
        self.b_tcl = create_file(join(self.modules_folder, "apa", "scoped_constraints", "b.tcl"))

        # A library with only test files
        self.c_vhd = create_file(join(self.modules_folder, "zebra", "test", "c.vhd"))

        modules = get_modules([self.modules_folder])

        # Use OrderedDict here in test so that order will be preserved and we can test for equality.
        # In real world case a normal dict can be used.
        generics = OrderedDict(enable=True, disable=False, integer=123, slv="4'b0101")

        self.tcl = VivadoTcl(name="name", modules=modules, part="part", top="top", block_design=None, generics=generics, constraints=[])

    def test_only_synthesis_files_added_to_create_project_tcl(self):
        tcl = self.tcl.create(project_folder="")
        assert self.a_vhd in tcl and self.b_vhd in tcl
        assert self.tb_a_vhd not in tcl and "tb_a.vhd" not in tcl

    def test_empty_library_not_in_create_project_tcl(self):
        tcl = self.tcl.create(project_folder="")
        assert "zebra" not in tcl

    def test_generics(self):
        tcl = self.tcl.create(project_folder="")
        expected = "\nset_property generic {enable=1'b1 disable=1'b0 integer=123 slv=4'b0101} [current_fileset]\n"
        assert expected in tcl

    def test_constraints(self):
        tcl = self.tcl.create(project_folder="")

        expected = "\nread_xdc -ref a %s\n" % abspath(self.a_xdc)
        assert expected in tcl
        expected = "\nread_xdc -ref b -unmanaged %s\n" % abspath(self.b_tcl)
        assert expected in tcl
