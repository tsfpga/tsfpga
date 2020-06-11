# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from collections import OrderedDict
from pathlib import Path
import unittest

import pytest

from tsfpga.build_step_tcl_hook import BuildStepTclHook
from tsfpga.module import get_modules
from tsfpga.system_utils import create_file
from tsfpga.vivado_tcl import VivadoTcl
from tsfpga.vivado_utils import to_tcl_path
from tsfpga.test.test_utils import file_contains_string


def test_set_create_run_index():
    tcl = VivadoTcl(name="").create(
        project_folder=Path(),
        modules=[],
        part="",
        top="",
        run_index=2
    )
    assert "\ncurrent_run [get_runs synth_2]\n" in tcl


def test_static_generics():
    # Use OrderedDict here in test so that order will be preserved and we can test for equality.
    # In real world case a normal dict can be used.
    generics = OrderedDict(enable=True, disable=False, integer=123, slv="4'b0101")

    tcl = VivadoTcl(name="").create(
        project_folder=Path(),
        modules=[],
        part="",
        top="",
        run_index=1,
        generics=generics
    )
    expected = "\nset_property generic {enable=1'b1 disable=1'b0 integer=123 slv=4'b0101} [current_fileset]\n"
    assert expected in tcl


def test_build_step_hooks():
    dummy = BuildStepTclHook(Path("dummy.tcl"), "STEPS.SYNTH_DESIGN.TCL.PRE")
    files = BuildStepTclHook(Path("files.tcl"), "STEPS.ROUTE_DESIGN.TCL.PRE")
    tcl = VivadoTcl(name="").create(
        project_folder=Path(),
        modules=[],
        part="part",
        top="",
        run_index=1,
        build_step_hooks=[dummy, files]
    )

    assert f"\nset_property STEPS.SYNTH_DESIGN.TCL.PRE {to_tcl_path(dummy.tcl_file)} ${{run}}\n" in tcl
    assert f"\nset_property STEPS.ROUTE_DESIGN.TCL.PRE {to_tcl_path(files.tcl_file)} ${{run}}\n" in tcl


def test_build_step_hooks_with_same_hook_step(tmp_path):
    dummy = BuildStepTclHook(Path("dummy.tcl"), "STEPS.SYNTH_DESIGN.TCL.PRE")
    files = BuildStepTclHook(Path("files.tcl"), "STEPS.SYNTH_DESIGN.TCL.PRE")
    tcl = VivadoTcl(name="").create(
        project_folder=tmp_path / "dummy_project_folder",
        modules=[],
        part="part",
        top="",
        run_index=1,
        build_step_hooks=[dummy, files]
    )

    hook_file = tmp_path / "dummy_project_folder" / "hook_STEPS_SYNTH_DESIGN_TCL_PRE.tcl"

    assert file_contains_string(hook_file, f"source {to_tcl_path(dummy.tcl_file)}")
    assert file_contains_string(hook_file, f"source {to_tcl_path(files.tcl_file)}")

    assert f"\nset_property STEPS.SYNTH_DESIGN.TCL.PRE {to_tcl_path(hook_file)} ${{run}}\n" in tcl


def test_ip_cache_location(tmp_path):
    tcl = VivadoTcl(name="").create(
        project_folder=Path(),
        modules=[],
        part="part",
        top="",
        run_index=1
    )
    assert "config_ip_cache" not in tcl

    tcl = VivadoTcl(name="").create(
        project_folder=Path(),
        modules=[],
        part="part",
        top="",
        run_index=1,
        ip_cache_path=tmp_path
    )
    assert f"\nconfig_ip_cache -use_cache_location {to_tcl_path(tmp_path)}\n" in tcl


def test_set_multiple_threads():
    num_threads = 2
    tcl = VivadoTcl(name="").build(
        project_file=Path(),
        output_path=Path(),
        num_threads=num_threads,
        run_index=1
    )
    assert "set_param general.maxThreads %d" % num_threads in tcl
    assert "launch_runs synth_1 -jobs %d" % num_threads in tcl
    assert "launch_runs impl_1 -jobs %d" % num_threads in tcl


def test_set_build_run_index():
    tcl = VivadoTcl(name="").build(
        project_file=Path(),
        output_path=Path(),
        num_threads=0,
        run_index=1
    )
    assert "impl_1" in tcl
    assert "synth_1" in tcl
    assert "impl_2" not in tcl
    assert "synth_2" not in tcl

    tcl = VivadoTcl(name="").build(
        project_file=Path(),
        output_path=Path(),
        num_threads=0,
        run_index=2
    )
    assert "impl_2" in tcl
    assert "synth_2" in tcl
    assert "impl_1" not in tcl
    assert "synth_1" not in tcl


def test_runtime_generics():
    tcl = VivadoTcl(name="").build(
        project_file=Path(),
        output_path=Path(),
        num_threads=0,
        run_index=0,
        generics=dict(dummy=True)
    )
    expected = "\nset_property generic {dummy=1'b1} [current_fileset]\n"
    assert expected in tcl


# pylint: disable=too-many-instance-attributes
@pytest.mark.usefixtures("fixture_tmp_path")
class TestVivadoTcl(unittest.TestCase):

    tmp_path = None

    def setUp(self):
        self.modules_folder = self.tmp_path / "modules"

        # A library with some synth files and some test files
        self.a_vhd = to_tcl_path(create_file(self.modules_folder / "apa" / "a.vhd"))
        self.tb_a_vhd = to_tcl_path(create_file(self.modules_folder / "apa" / "test" / "tb_a.vhd"))
        self.a_xdc = to_tcl_path(create_file(self.modules_folder / "apa" / "scoped_constraints" / "a.xdc"))

        self.b_v = to_tcl_path(create_file(self.modules_folder / "apa" / "b.v"))
        self.b_tcl = to_tcl_path(create_file(self.modules_folder / "apa" / "scoped_constraints" / "b.tcl"))

        self.c_tcl = to_tcl_path(create_file(self.modules_folder / "apa" / "ip_cores" / "c.tcl"))

        # A library with only test files
        self.c_vhd = to_tcl_path(create_file(self.modules_folder / "zebra" / "test" / "c.vhd"))

        self.modules = get_modules([self.modules_folder])

        self.tcl = VivadoTcl(name="name")

    def test_only_synthesis_files_added_to_create_project_tcl(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="",
            top="",
            run_index=1
        )
        assert self.a_vhd in tcl and self.b_v in tcl
        assert self.tb_a_vhd not in tcl and "tb_a.vhd" not in tcl

    def test_different_hdl_file_types(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="",
            top="",
            run_index=1
        )
        assert f"read_vhdl -library apa -vhdl2008 {{{self.a_vhd}}}" in tcl
        assert f"read_verilog {{{self.b_v}}}" in tcl

    def test_constraints(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            run_index=1
        )

        expected = "\nread_xdc -ref a %s\n" % self.a_xdc
        assert expected in tcl
        expected = "\nread_xdc -ref b -unmanaged %s\n" % self.b_tcl
        assert expected in tcl

    def test_ip_core_files(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            run_index=1
        )
        assert "\nsource -notrace %s\n" % self.c_tcl in tcl

    def test_empty_library_not_in_create_project_tcl(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            run_index=1
        )
        assert "zebra" not in tcl

    def test_multiple_tcl_sources(self):
        extra_tcl_sources = [Path("dummy.tcl"), Path("files.tcl")]
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            run_index=1,
            tcl_sources=extra_tcl_sources
        )

        for filename in extra_tcl_sources:
            assert f"\nsource -notrace {to_tcl_path(filename)}\n" in tcl

    def test_io_buffer_setting(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            run_index=1,
            disable_io_buffers=True
        )

        no_io_buffers_tcl = "\nset_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} -value -no_iobuf -objects [get_runs synth_1]\n"
        assert no_io_buffers_tcl in tcl

        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            run_index=1,
            disable_io_buffers=False
        )

        assert no_io_buffers_tcl not in tcl
