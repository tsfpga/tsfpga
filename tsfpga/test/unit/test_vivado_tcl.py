# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import dirname, join
import unittest
from collections import OrderedDict

from tsfpga.module import get_modules
from tsfpga.system_utils import create_file, delete
from tsfpga.vivado_tcl import VivadoTcl
from tsfpga.vivado_utils import to_tcl_path


THIS_DIR = dirname(__file__)


class TestVivadoTcl(unittest.TestCase):  # pylint: disable=too-many-instance-attributes

    modules_folder = join(THIS_DIR, "modules")

    def setUp(self):
        delete(self.modules_folder)

        # A library with some synth files and some test files
        self.a_vhd = to_tcl_path(create_file(join(self.modules_folder, "apa", "a.vhd")))
        self.tb_a_vhd = to_tcl_path(create_file(join(self.modules_folder, "apa", "test", "tb_a.vhd")))
        self.a_xdc = to_tcl_path(create_file(join(self.modules_folder, "apa", "scoped_constraints", "a.xdc")))

        self.b_v = to_tcl_path(create_file(join(self.modules_folder, "apa", "b.v")))
        self.b_tcl = to_tcl_path(create_file(join(self.modules_folder, "apa", "scoped_constraints", "b.tcl")))

        self.c_tcl = to_tcl_path(create_file(join(self.modules_folder, "apa", "ip_cores", "c.tcl")))

        # A library with only test files
        self.c_vhd = to_tcl_path(create_file(join(self.modules_folder, "zebra", "test", "c.vhd")))

        self.modules = get_modules([self.modules_folder])

        self.tcl = VivadoTcl(name="name")

    def test_only_synthesis_files_added_to_create_project_tcl(self):
        tcl = self.tcl.create(
            part="",
            modules=self.modules,
            top="",
            tcl_sources=[],
            generics=None,
            constraints=[],
            project_folder="",
            ip_cache_path="",
        )
        assert self.a_vhd in tcl and self.b_v in tcl
        assert self.tb_a_vhd not in tcl and "tb_a.vhd" not in tcl

    def test_different_hdl_file_types(self):
        tcl = self.tcl.create(
            part="",
            modules=self.modules,
            top="",
            tcl_sources=[],
            generics=None,
            constraints=[],
            project_folder="",
            ip_cache_path="",
        )
        assert f"read_vhdl -library apa -vhdl2008 {{{self.a_vhd}}}" in tcl
        assert f"read_verilog {{{self.b_v}}}" in tcl

    def test_empty_library_not_in_create_project_tcl(self):
        tcl = self.tcl.create(
            part="",
            modules=self.modules,
            top="",
            tcl_sources=[],
            generics=None,
            constraints=[],
            project_folder="",
            ip_cache_path="",
        )
        assert "zebra" not in tcl

    def test_static_generics(self):
        # Use OrderedDict here in test so that order will be preserved and we can test for equality.
        # In real world case a normal dict can be used.
        generics = OrderedDict(enable=True, disable=False, integer=123, slv="4'b0101")

        tcl = self.tcl.create(
            part="part",
            modules=self.modules,
            top="",
            tcl_sources=[],
            generics=generics,
            constraints=[],
            project_folder="",
            ip_cache_path="",
        )
        expected = "\nset_property generic {enable=1'b1 disable=1'b0 integer=123 slv=4'b0101} [current_fileset]\n"
        assert expected in tcl

    def test_constraints(self):
        tcl = self.tcl.create(
            part="part",
            modules=self.modules,
            top="",
            tcl_sources=[],
            generics=None,
            constraints=[],
            project_folder="",
            ip_cache_path="",
        )

        expected = "\nread_xdc -ref a %s\n" % self.a_xdc
        assert expected in tcl
        expected = "\nread_xdc -ref b -unmanaged %s\n" % self.b_tcl
        assert expected in tcl

    def test_multiple_tcl_sources(self):
        extra_tcl_sources = ["dummy.tcl", "files.tcl"]
        tcl = self.tcl.create(
            part="part",
            modules=self.modules,
            top="",
            tcl_sources=extra_tcl_sources,
            generics=None,
            constraints=[],
            project_folder="",
            ip_cache_path="",
        )

        for filename in extra_tcl_sources:
            assert f"\nsource -notrace {to_tcl_path(filename)}\n" in tcl

    def test_ip_core_files(self):
        tcl = self.tcl.create(
            part="part",
            modules=self.modules,
            top="",
            tcl_sources=[],
            generics=None,
            constraints=[],
            project_folder="",
            ip_cache_path="",
        )
        assert "\nsource -notrace %s\n" % self.c_tcl in tcl

    def test_ip_cache_location(self):
        tcl = self.tcl.create(
            part="part",
            modules=self.modules,
            top="",
            tcl_sources=[],
            generics=None,
            constraints=[],
            project_folder="",
            ip_cache_path=None,
        )
        assert "config_ip_cache" not in tcl

        ip_cache_location = to_tcl_path(THIS_DIR)
        tcl = self.tcl.create(
            part="part",
            modules=self.modules,
            top="",
            tcl_sources=[],
            generics=None,
            constraints=[],
            project_folder="",
            ip_cache_path=ip_cache_location,
        )
        assert f"\nconfig_ip_cache -use_cache_location {ip_cache_location}\n" in tcl

    def test_set_multiple_threads(self):
        num_threads = 2
        tcl = self.tcl.build(project_file="", output_path="", generics=None, synth_only=False, num_threads=num_threads)
        assert "set_param general.maxThreads %d" % num_threads in tcl
        assert "launch_runs synth_1 -jobs %d" % num_threads in tcl
        assert "launch_runs impl_1 -jobs %d" % num_threads in tcl

    def test_runtime_generics(self):
        generics = dict(dummy=True)
        tcl = self.tcl.create(
            part="part",
            modules=self.modules,
            top="",
            tcl_sources=[],
            generics=generics,
            constraints=[],
            project_folder="",
            ip_cache_path="",
        )
        expected = "\nset_property generic {dummy=1'b1} [current_fileset]\n"
        assert expected in tcl
