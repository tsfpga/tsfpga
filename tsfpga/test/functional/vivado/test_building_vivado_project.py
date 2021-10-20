# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import sys
import unittest

import pytest

import tsfpga
from tsfpga.constraint import Constraint
from tsfpga.module import get_modules, get_hdl_modules
from tsfpga.system_utils import create_file, run_command
from tsfpga.vivado.build_result_checker import LessThan, TotalLuts
from tsfpga.vivado.project import VivadoNetlistProject, VivadoProject
from tsfpga.test import file_contains_string


def test_building_artyz7_project(tmp_path):
    build_py = tsfpga.TSFPGA_EXAMPLES / "build.py"
    cmd = [
        sys.executable,
        build_py,
        "artyz7",
        "--projects-path",
        tmp_path / "projects",
        "--output-path",
        tmp_path / "artifacts",
    ]
    run_command(cmd, cwd=tsfpga.REPO_ROOT)
    assert (tmp_path / "artifacts" / "artyz7" / "artyz7.bit").exists()
    assert (tmp_path / "artifacts" / "artyz7" / "artyz7.bin").exists()
    assert (tmp_path / "artifacts" / "artyz7" / "artyz7.xsa").exists()
    assert (tmp_path / "artifacts" / "artyz7" / "artyz7-0.0.0.0.zip").exists()


# pylint: disable=too-many-instance-attributes
@pytest.mark.usefixtures("fixture_tmp_path")
class TestBasicProject(unittest.TestCase):

    tmp_path = None

    top_template = """
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library resync;


entity test_proj_top is
  port (
    clk_in : in std_logic;
    input : in std_logic;
    clk_out : in std_logic;
    output : out std_logic
  );
end entity;

architecture a of test_proj_top is
  signal input_p1 : std_logic;
begin

  pipe_input : process
  begin
    wait until rising_edge(clk_in);
    input_p1 <= input;
  end process;

{code_block}

end architecture;
"""

    def setUp(self):
        modules_folder = self.tmp_path / "modules"
        self.project_folder = self.tmp_path / "vivado"

        # Default top level
        resync = """
  code_block : entity resync.resync_level
  generic map (
    enable_input_register => false
  )
  port map (
    data_in => input_p1,

    clk_out => clk_out,
    data_out => output
  );"""
        top = self.top_template.format(code_block=resync)
        self.top_file = create_file(modules_folder / "apa" / "test_proj_top.vhd", top)

        self.constraint_io = """
set_property -dict {package_pin H16 iostandard lvcmos33} [get_ports clk_in]
set_property -dict {package_pin P14 iostandard lvcmos33} [get_ports input]
set_property -dict {package_pin K17 iostandard lvcmos33} [get_ports clk_out]
set_property -dict {package_pin T16 iostandard lvcmos33} [get_ports output]
"""
        constraint_clocks = """
# 250 MHz
create_clock -period 4 -name clk_in [get_ports clk_in]
create_clock -period 4 -name clk_out [get_ports clk_out]
"""
        self.constraint_file = create_file(
            modules_folder / "apa" / "test_proj_pinning.tcl", self.constraint_io + constraint_clocks
        )
        constraints = [Constraint(self.constraint_file)]

        self.modules = get_hdl_modules() + get_modules([modules_folder])
        self.proj = VivadoProject(
            name="test_proj",
            modules=self.modules,
            part="xc7z020clg400-1",
            constraints=constraints,
            # Faster
            default_run_index=2,
        )
        self.log_file = self.project_folder / "vivado.log"
        self.runs_folder = self.project_folder / "test_proj.runs"

    def _create_vivado_project(self):
        assert self.proj.create(self.project_folder)

    def test_create_project(self):
        self._create_vivado_project()

    def test_synth_project(self):
        self._create_vivado_project()
        build_result = self.proj.build(self.project_folder, synth_only=True)
        assert build_result.success
        assert (self.runs_folder / "synth_2" / "hierarchical_utilization.rpt").exists()

    def test_synth_should_fail_if_source_code_does_not_compile(self):
        create_file(self.top_file, "garbage\napa\nhest")

        self._create_vivado_project()

        build_result = self.proj.build(self.project_folder, synth_only=True)
        assert not build_result.success
        assert file_contains_string(self.log_file, "\nERROR: Run synth_2 failed.")

    def test_synth_with_assert_false_should_fail(self):
        assert_false = """
  assert false severity failure;"""

        top = self.top_template.format(code_block=assert_false)
        create_file(self.top_file, top)

        self._create_vivado_project()

        build_result = self.proj.build(self.project_folder, synth_only=True, run_index=2)
        assert not build_result.success
        assert file_contains_string(self.log_file, 'RTL assertion: "Assertion violation."')

    def test_build_project(self):
        self._create_vivado_project()
        build_result = self.proj.build(self.project_folder, self.project_folder)

        assert (self.project_folder / (self.proj.name + ".bit")).exists()
        assert (self.project_folder / (self.proj.name + ".bin")).exists()
        assert (self.runs_folder / "impl_2" / "hierarchical_utilization.rpt").exists()

        # Sanity check some of the build result
        assert build_result.success

        assert build_result.synthesis_size["Total LUTs"] == 0, build_result.synthesis_size

        assert build_result.implementation_size["FFs"] > 0, build_result.implementation_size
        assert build_result.implementation_size["FFs"] < 2000, build_result.implementation_size

    def test_build_with_bad_setup_timing_should_fail(self):
        # Do a ridiculously wide multiplication, which Vivado can't optimize away
        bad_timing = """
  mult_block : block
    signal resynced_input : std_logic;
  begin
    resync_level_inst : entity resync.resync_level
    generic map (
      enable_input_register => false
    )
    port map (
      data_in => input_p1,

      clk_out => clk_out,
      data_out => resynced_input
    );

    mult : process
      constant bit_pattern : std_logic_vector(32 -1 downto 0) := x"deadbeef";
      variable term1, term2, term3 : unsigned(bit_pattern'range);
    begin
      wait until rising_edge(clk_out);
      term1 := unsigned(bit_pattern);
      term1(28) := resynced_input;

      term2 := unsigned(not bit_pattern);
      term2(22) := resynced_input;

      output <= xor (term1 * term2);
    end process;
  end block;"""

        top = self.top_template.format(code_block=bad_timing)
        create_file(self.top_file, top)

        self._create_vivado_project()

        build_result = self.proj.build(self.project_folder, self.project_folder)
        assert not build_result.success
        assert file_contains_string(
            self.log_file, "\nERROR: Setup/hold timing not OK after implementation run."
        )

        assert (self.runs_folder / "impl_2" / "timing_summary.rpt").exists()

    def test_build_with_unhandled_clock_crossing_should_fail(self):
        bad_resync = """
  pipe_output : process
  begin
    wait until rising_edge(clk_out);
    output <= input_p1;
  end process;"""

        top = self.top_template.format(code_block=bad_resync)
        create_file(self.top_file, top)

        self._create_vivado_project()

        build_result = self.proj.build(self.project_folder, self.project_folder)
        assert not build_result.success
        assert file_contains_string(
            self.log_file, "\nERROR: Unhandled clock crossing in synth_2 run."
        )

        assert (self.runs_folder / "synth_2" / "hierarchical_utilization.rpt").exists()
        assert (self.runs_folder / "synth_2" / "timing_summary.rpt").exists()
        assert (self.runs_folder / "synth_2" / "clock_interaction.rpt").exists()

    def test_build_with_bad_pulse_width_timing_should_fail(self):
        # Overwrite the default constraint file
        constraint_clocks = """
# 250 MHz, but duty cycle is only 0.2 ns
create_clock -period 4 -waveform {1.0 1.2} -name clk_in [get_ports clk_in]
create_clock -period 4 -waveform {1.0 1.2} -name clk_out [get_ports clk_out]
"""
        create_file(self.constraint_file, self.constraint_io + constraint_clocks)

        self._create_vivado_project()

        build_result = self.proj.build(self.project_folder, self.project_folder)
        assert not build_result.success
        assert file_contains_string(
            self.log_file, "\nERROR: Pulse width timing violation after implementation run."
        )

        assert (self.runs_folder / "impl_2" / "pulse_width.rpt").exists()

    def test_building_vivado_netlist_project(self):
        project = VivadoNetlistProject(
            name="test_proj",
            modules=self.modules,
            part="xc7z020clg400-1",
            # Faster
            default_run_index=2,
            build_result_checkers=[TotalLuts(LessThan(1000))],
        )
        assert project.create(self.project_folder)

        build_result = project.build(
            project_path=self.project_folder, output_path=self.project_folder
        )
        assert build_result.success
        assert (self.runs_folder / "synth_2" / "hierarchical_utilization.rpt").exists()
