# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import unittest
from collections import OrderedDict
from pathlib import Path
from unittest.mock import MagicMock

# Third party libraries
import pytest

# First party libraries
from tsfpga.build_step_tcl_hook import BuildStepTclHook
from tsfpga.ip_core_file import IpCoreFile
from tsfpga.module import BaseModule, get_modules
from tsfpga.system_utils import create_file
from tsfpga.test import file_contains_string

# pylint: disable=unused-import
from tsfpga.test.conftest import fixture_tmp_path  # noqa: F401
from tsfpga.vivado.common import to_tcl_path
from tsfpga.vivado.generics import BitVectorGenericValue, StringGenericValue
from tsfpga.vivado.tcl import VivadoTcl


def test_set_create_run_index():
    tcl = VivadoTcl(name="").create(project_folder=Path(), modules=[], part="", top="", run_index=2)
    assert "\ncurrent_run [get_runs synth_2]\n" in tcl


def test_static_generics():
    # Use OrderedDict here in test so that order will be preserved and we can test for equality.
    # In real world case a normal dict can be used.
    generics = OrderedDict(
        enable=True,
        disable=False,
        integer=123,
        slv=BitVectorGenericValue("0101"),
        string=StringGenericValue("apa"),
    )

    tcl = VivadoTcl(name="").create(
        project_folder=Path(), modules=[], part="", top="", run_index=1, generics=generics
    )
    expected = (
        "\nset_property generic {enable=1'b1 disable=1'b0 integer=123 slv=4'b0101 string=apa} "
        "[current_fileset]\n"
    )
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
        build_step_hooks=[dummy, files],
    )

    assert (
        f"\nset_property STEPS.SYNTH_DESIGN.TCL.PRE {{{to_tcl_path(dummy.tcl_file)}}} ${{run}}\n"
        in tcl
    )
    assert (
        f"\nset_property STEPS.ROUTE_DESIGN.TCL.PRE {{{to_tcl_path(files.tcl_file)}}} ${{run}}\n"
        in tcl
    )


def test_build_step_hooks_with_same_hook_step(tmp_path):
    dummy = BuildStepTclHook(Path("dummy.tcl"), "STEPS.SYNTH_DESIGN.TCL.PRE")
    files = BuildStepTclHook(Path("files.tcl"), "STEPS.SYNTH_DESIGN.TCL.PRE")
    tcl = VivadoTcl(name="").create(
        project_folder=tmp_path / "dummy_project_folder",
        modules=[],
        part="part",
        top="",
        run_index=1,
        build_step_hooks=[dummy, files],
    )

    hook_file = tmp_path / "dummy_project_folder" / "hook_STEPS_SYNTH_DESIGN_TCL_PRE.tcl"

    assert file_contains_string(hook_file, f"source {{{to_tcl_path(dummy.tcl_file)}}}")
    assert file_contains_string(hook_file, f"source {{{to_tcl_path(files.tcl_file)}}}")

    assert (
        f"\nset_property STEPS.SYNTH_DESIGN.TCL.PRE {{{to_tcl_path(hook_file)}}} ${{run}}\n" in tcl
    )


def test_ip_cache_location(tmp_path):
    tcl = VivadoTcl(name="").create(
        project_folder=Path(), modules=[], part="part", top="", run_index=1
    )
    assert "config_ip_cache" not in tcl

    tcl = VivadoTcl(name="").create(
        project_folder=Path(), modules=[], part="part", top="", run_index=1, ip_cache_path=tmp_path
    )
    assert f"\nconfig_ip_cache -use_cache_location {{{to_tcl_path(tmp_path)}}}\n" in tcl


def test_multiple_threads_is_capped_by_vivado_limits():
    num_threads = 128
    tcl = VivadoTcl(name="").build(
        project_file=Path(), output_path=Path(), num_threads=num_threads, run_index=1
    )
    print(tcl)
    assert "set_param general.maxThreads 32" in tcl
    assert "set_param synth.maxThreads 8" in tcl
    assert "launch_runs ${run} -jobs 128" in tcl
    assert "launch_runs ${run} -jobs 128" in tcl


def test_set_build_run_index():
    tcl = VivadoTcl(name="").build(
        project_file=Path(), output_path=Path(), num_threads=0, run_index=1
    )
    assert "impl_1" in tcl
    assert "synth_1" in tcl
    assert "impl_2" not in tcl
    assert "synth_2" not in tcl

    tcl = VivadoTcl(name="").build(
        project_file=Path(), output_path=Path(), num_threads=0, run_index=2
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
        generics=dict(dummy=True),
    )
    expected = "\nset_property generic {dummy=1'b1} [current_fileset]\n"
    assert expected in tcl


def test_build_with_synth_only():
    tcl = VivadoTcl(name="").build(
        project_file=Path(), output_path=Path(), num_threads=0, run_index=0, synth_only=False
    )
    assert "synth_" in tcl
    assert "impl_" in tcl

    tcl = VivadoTcl(name="").build(
        project_file=Path(), output_path=Path(), num_threads=0, run_index=0, synth_only=True
    )
    assert "synth_" in tcl
    assert "impl_" not in tcl


def test_build_with_from_impl():
    tcl = VivadoTcl(name="").build(
        project_file=Path(), output_path=Path(), num_threads=0, run_index=0, from_impl=False
    )
    assert "synth_" in tcl
    assert "impl_" in tcl

    tcl = VivadoTcl(name="").build(
        project_file=Path(), output_path=Path(), num_threads=0, run_index=0, from_impl=True
    )
    assert "synth_" not in tcl
    assert "impl_" in tcl


def test_module_getters_are_called_with_correct_arguments():
    modules = [MagicMock(spec=BaseModule)]
    VivadoTcl(name="").create(
        project_folder=Path(),
        modules=modules,
        part="",
        top="",
        run_index=1,
        other_arguments=dict(apa=123, hest=456),
    )

    modules[0].get_synthesis_files.assert_called_once_with(apa=123, hest=456)
    modules[0].get_scoped_constraints.assert_called_once_with(apa=123, hest=456)
    modules[0].get_ip_core_files.assert_called_once_with(apa=123, hest=456)


# pylint: disable=too-many-instance-attributes
@pytest.mark.usefixtures("fixture_tmp_path")
class TestVivadoTcl(unittest.TestCase):
    tmp_path = None

    def setUp(self):
        self.modules_folder = self.tmp_path / "modules"

        # A library with some synth files and some test files
        self.a_vhd = to_tcl_path(create_file(self.modules_folder / "apa" / "a.vhd"))
        self.b_vhd = to_tcl_path(create_file(self.modules_folder / "apa" / "b.vhd"))
        self.tb_a_vhd = to_tcl_path(create_file(self.modules_folder / "apa" / "test" / "tb_a.vhd"))
        self.a_xdc = to_tcl_path(
            create_file(self.modules_folder / "apa" / "scoped_constraints" / "a.xdc")
        )

        self.c_v = to_tcl_path(create_file(self.modules_folder / "apa" / "c.v"))
        self.b_tcl = to_tcl_path(
            create_file(self.modules_folder / "apa" / "scoped_constraints" / "b.tcl")
        )

        self.c_tcl = to_tcl_path(create_file(self.modules_folder / "apa" / "ip_cores" / "c.tcl"))

        # A library with only test files
        self.d_vhd = to_tcl_path(create_file(self.modules_folder / "zebra" / "test" / "d.vhd"))

        self.modules = get_modules([self.modules_folder])

        self.tcl = VivadoTcl(name="name")

    def test_source_file_list_is_correctly_formatted(self):
        tcl = self.tcl.create(
            project_folder=Path(), modules=self.modules, part="", top="", run_index=1
        )

        # Order of files is not really deterministic
        expected_1 = f"\nread_vhdl -library apa -vhdl2008 {{{{{self.b_vhd}}} {{{self.a_vhd}}}}}\n"
        expected_2 = f"\nread_vhdl -library apa -vhdl2008 {{{{{self.a_vhd}}} {{{self.b_vhd}}}}}\n"
        assert expected_1 in tcl or expected_2 in tcl

        expected = f"\nread_verilog {{{self.c_v}}}\n"
        assert expected in tcl

    def test_only_synthesis_files_added_to_create_project_tcl(self):
        tcl = self.tcl.create(
            project_folder=Path(), modules=self.modules, part="", top="", run_index=1
        )
        assert self.a_vhd in tcl and self.c_v in tcl
        assert self.tb_a_vhd not in tcl and "tb_a.vhd" not in tcl

    def test_constraints(self):
        tcl = self.tcl.create(
            project_folder=Path(), modules=self.modules, part="part", top="", run_index=1
        )

        expected = f"\nread_xdc -ref a {{{self.a_xdc}}}\n"
        assert expected in tcl
        expected = f"\nread_xdc -ref b -unmanaged {{{self.b_tcl}}}\n"
        assert expected in tcl

    def test_ip_core_files(self):
        ip_core_file_path = self.tmp_path / "my_name.tcl"
        module = MagicMock(spec=BaseModule)
        module.get_ip_core_files.return_value = [
            IpCoreFile(path=ip_core_file_path, apa="hest", zebra=123)
        ]

        self.modules.append(module)

        tcl = self.tcl.create(
            project_folder=Path(), modules=self.modules, part="part", top="", run_index=1
        )

        assert (
            f"""
proc create_ip_core_c {{}} {{
  source -notrace {{{self.c_tcl}}}
}}
create_ip_core_c
"""
            in tcl
        )

        assert (
            f"""
proc create_ip_core_my_name {{}} {{
  set apa "hest"
  set zebra "123"
  source -notrace {{{to_tcl_path(ip_core_file_path)}}}
}}
create_ip_core_my_name
"""
            in tcl
        )

    def test_create_with_ip_cores_only(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            run_index=1,
            ip_cores_only=True,
        )
        assert self.c_tcl in tcl
        assert self.a_vhd not in tcl

    def test_empty_library_not_in_create_project_tcl(self):
        tcl = self.tcl.create(
            project_folder=Path(), modules=self.modules, part="part", top="", run_index=1
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
            tcl_sources=extra_tcl_sources,
        )

        for filename in extra_tcl_sources:
            assert f"\nsource -notrace {{{to_tcl_path(filename)}}}\n" in tcl

    def test_io_buffer_setting(self):
        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            run_index=1,
            disable_io_buffers=True,
        )

        no_io_buffers_tcl = (
            "\nset_property -name {STEPS.SYNTH_DESIGN.ARGS.MORE OPTIONS} "
            "-value -no_iobuf -objects [get_runs synth_1]\n"
        )
        assert no_io_buffers_tcl in tcl

        tcl = self.tcl.create(
            project_folder=Path(),
            modules=self.modules,
            part="part",
            top="",
            run_index=1,
            disable_io_buffers=False,
        )

        assert no_io_buffers_tcl not in tcl

    def test_analyze_synthesis_settings_on_and_off(self):
        tcl = self.tcl.build(
            project_file=Path(),
            output_path=Path(),
            num_threads=1,
            run_index=1,
            analyze_synthesis_timing=True,
        )
        assert "open_run" in tcl
        assert "report_clock_interaction" in tcl

        tcl = self.tcl.build(
            project_file=Path(),
            output_path=Path(),
            num_threads=1,
            run_index=1,
            analyze_synthesis_timing=False,
        )
        # When disabled, the run should not even be opened, which saves time
        assert "open_run" not in tcl
        assert "report_clock_interaction" not in tcl
