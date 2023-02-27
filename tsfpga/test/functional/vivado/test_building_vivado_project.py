# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import sys
import unittest

# Third party libraries
import pytest

# First party libraries
import tsfpga
from tsfpga.constraint import Constraint
from tsfpga.examples.example_env import get_hdl_modules
from tsfpga.module import get_modules
from tsfpga.system_utils import create_file, run_command
from tsfpga.test import file_contains_string
from tsfpga.vivado.build_result_checker import LessThan, TotalLuts
from tsfpga.vivado.project import VivadoNetlistProject, VivadoProject


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
    assert (tmp_path / "artifacts" / "artyz7" / "artyz7-0.0.0.zip").exists()


# pylint: disable=too-many-instance-attributes
@pytest.mark.usefixtures("fixture_tmp_path")
class TestBasicProject(unittest.TestCase):
    tmp_path = None

    top_template = """
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library common;
use common.attribute_pkg.all;

library resync;


entity test_proj_top is
  port (
    clk_in : in std_ulogic;
    input : in std_ulogic;
    clk_out : in std_ulogic;
    output : out std_ulogic
  );
end entity;

architecture a of test_proj_top is
  signal input_p1 : std_ulogic;
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
        module_folder = self.tmp_path / "modules" / "apa"

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
        self.top_file = create_file(module_folder / "test_proj_top.vhd", top)

        self.constraint_io = """
set_property -dict {package_pin H16 iostandard lvcmos33} [get_ports clk_in]
set_property -dict {package_pin P14 iostandard lvcmos33} [get_ports input]
set_property -dict {package_pin K17 iostandard lvcmos33} [get_ports clk_out]
set_property -dict {package_pin T16 iostandard lvcmos33} [get_ports output]
"""
        self.constraint_clocks = """
# 250 MHz
create_clock -period 4 -name clk_in [get_ports clk_in]
create_clock -period 4 -name clk_out [get_ports clk_out]
"""
        self.constraint_file = create_file(
            file=module_folder / "test_proj_pinning.tcl",
            contents=self.constraint_io + self.constraint_clocks,
        )
        constraints = [Constraint(self.constraint_file)]

        self.modules = get_hdl_modules() + get_modules(modules_folders=[module_folder.parent])
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

    @property
    def create_files(self):
        """
        Files that should exist when the project has been created.
        """
        return [self.project_folder / "test_proj.xpr"]

    @property
    def synthesis_files(self):
        """
        Files that should exist when the project has been synthesized.
        """
        return [self.runs_folder / "synth_2" / "hierarchical_utilization.rpt"]

    @property
    def build_files(self):
        """
        Files that should exist when the project has been fully built.
        """
        return [
            self.project_folder / f"{self.proj.name}.bit",
            self.project_folder / f"{self.proj.name}.bin",
            self.runs_folder / "impl_2" / "hierarchical_utilization.rpt",
        ]

    def _create_vivado_project(self):
        assert self.proj.create(self.project_folder)

        for path in self.create_files:
            assert path.exists(), path

    def test_create_project(self):
        self._create_vivado_project()

    def test_synth_project(self):
        self._create_vivado_project()

        build_result = self.proj.build(self.project_folder, synth_only=True)
        assert build_result.success
        for path in self.synthesis_files:
            assert path.exists(), path

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

    def test_synth_with_error_message_should_fail(self):
        # Elevate the "Generic 'X' not present" message to ERROR, then set a generic that
        # does not exist. This will trigger an ERROR message, which should crash the build.
        self.proj.tcl_sources.append(
            create_file(
                self.tmp_path / "elevate_vivado_message.tcl",
                contents="set_msg_config -new_severity ERROR -id {Synth 8-3819}",
            )
        )
        self.proj.static_generics["non_existing"] = 1024

        self._create_vivado_project()

        build_result = self.proj.build(self.project_folder, synth_only=True)
        assert not build_result.success
        assert file_contains_string(self.log_file, "\nERROR: Run synth_2 failed.")
        assert file_contains_string(
            self.log_file, "\nERROR: Vivado has reported one or more ERROR messages. See build log."
        )

    def test_build_project(self):
        self._create_vivado_project()

        build_result = self.proj.build(self.project_folder, self.project_folder)
        assert build_result.success
        for path in self.synthesis_files + self.build_files:
            assert path.exists(), path

        # Sanity check some of the build result
        assert build_result.synthesis_size["Total LUTs"] == 0, build_result.synthesis_size

        assert build_result.implementation_size["FFs"] > 0, build_result.implementation_size
        assert build_result.implementation_size["FFs"] < 2000, build_result.implementation_size

    def test_build_project_in_steps(self):
        self._create_vivado_project()
        for path in self.synthesis_files + self.build_files:
            assert not path.exists(), path

        build_result = self.proj.build(self.project_folder, self.project_folder, synth_only=True)
        assert build_result.success
        for path in self.synthesis_files:
            assert path.exists(), path
        for path in self.build_files:
            assert not path.exists(), path

        build_result = self.proj.build(self.project_folder, self.project_folder, from_impl=True)
        assert build_result.success
        for path in self.synthesis_files + self.build_files:
            assert path.exists(), path

    def test_build_with_bad_setup_timing_should_fail(self):
        # Do a ridiculously wide multiplication, which Vivado can't optimize away
        bad_timing = """
  mult_block : block
    signal resynced_input : std_ulogic;
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
      constant bit_pattern : std_ulogic_vector(32 -1 downto 0) := x"deadbeef";
      variable term1, term2, term3 : u_unsigned(bit_pattern'range);
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

    def test_build_with_bad_bus_skew_should_fail(self):
        resync_wide_word = """
  resync_block : block
    signal input_word, result_word : std_ulogic_vector(0 to 32 - 1) := (others => '0');

    attribute dont_touch of result_word : signal is "true";
  begin

    input_process : process
    begin
      wait until rising_edge(clk_in);
      input_word <= (others => input_p1);
    end process;

    result_process : process
    begin
      wait until rising_edge(clk_out);
      result_word <= input_word;
    end process;

  end block;"""
        top = self.top_template.format(code_block=resync_wide_word)
        create_file(self.top_file, top)

        # Overwrite the default constraint file
        constraint_bus_skew = """
set input_word [get_cells resync_block.input_word_reg*]
set result_word [get_cells resync_block.result_word_reg*]

# The constraints below are the same as e.g. resync_counter.tcl.

# Vivado manages to solve ~1.2 ns skew, so the value below will not succeed
set_bus_skew -from ${input_word} -to ${result_word} 0.8

# Set max delay to exclude the clock crossing from regular timing analysis
set_max_delay -datapath_only -from ${input_word} -to ${result_word} 3
"""
        create_file(
            file=self.constraint_file,
            contents=self.constraint_io + self.constraint_clocks + constraint_bus_skew,
        )

        self._create_vivado_project()

        build_result = self.proj.build(self.project_folder, self.project_folder)
        assert not build_result.success
        assert file_contains_string(
            self.log_file, "\nERROR: Bus skew constraints not met after implementation run."
        )

        assert (self.runs_folder / "impl_2" / "bus_skew.rpt").exists()

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
        for path in self.synthesis_files:
            assert path.exists(), path
