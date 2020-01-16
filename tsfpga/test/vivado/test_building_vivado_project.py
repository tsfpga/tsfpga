# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import dirname, join, exists
import pytest
from subprocess import CalledProcessError
import sys
import unittest

import tsfpga
from tsfpga.constraint import Constraint
from tsfpga.module import get_modules
from tsfpga.system_utils import create_file, delete, run_command
from tsfpga.test import file_contains_string
from tsfpga.vivado_project import VivadoProject


THIS_DIR = dirname(__file__)


def test_building_artyz7_project(tmpdir):
    build_py = join(tsfpga.TSFPGA_EXAMPLES, "build.py")
    cmd = [
        sys.executable,
        build_py,
        "artyz7",
        "--project-path", tmpdir,
        "--output-path", tmpdir
    ]
    run_command(cmd, cwd=tsfpga.ROOT)
    assert exists(join(tmpdir, "artyz7.bit"))
    assert exists(join(tmpdir, "artyz7.bin"))
    assert exists(join(tmpdir, "artyz7.hdf"))


class TestBasicProject(unittest.TestCase):

    part = "xc7z020clg400-1"
    modules_folder = join(THIS_DIR, "modules")
    project_folder = join(THIS_DIR, "vivado")

    top_file = join(modules_folder, "apa", "test_proj_top.vhd")
    top_template = """
library ieee;
use ieee.std_logic_1164.all;

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

{assign_output}

end architecture;
"""

    resync = """
  assign_output : entity resync.resync_level
  port map (
    data_in => input_p1,

    clk_out => clk_out,
    data_out => output
  );"""

    unhandled_clock_crossing = """
  assign_output : process
  begin
    wait until rising_edge(clk_out);
    output <= input_p1;
  end process;"""

    constraint_file = join(modules_folder, "apa", "test_proj_pinning.tcl")
    constraints = """
set_property -dict {package_pin H16 iostandard lvcmos33} [get_ports clk_in]
set_property -dict {package_pin P14 iostandard lvcmos33} [get_ports input]
set_property -dict {package_pin K17 iostandard lvcmos33} [get_ports clk_out]
set_property -dict {package_pin T16 iostandard lvcmos33} [get_ports output]

# 200 MHz
create_clock -period 5 -name clk_in [get_ports clk_in]
create_clock -period 5 -name clk_out [get_ports clk_out]
"""

    def setUp(self):
        delete(self.modules_folder)
        delete(self.project_folder)

        self.top = self.top_template.format(assign_output=self.resync)  # Default top level

        create_file(self.top_file, self.top)
        create_file(self.constraint_file, self.constraints)
        constraints = [Constraint(self.constraint_file)]

        self.modules = get_modules([self.modules_folder, tsfpga.TSFPGA_MODULES])
        self.proj = VivadoProject(name="test_proj", modules=self.modules, part=self.part, constraints=constraints)
        self.proj.create(self.project_folder)

        self.log_file = join(self.project_folder, "vivado.log")

    def test_create_project(self):
        pass

    def test_synth_project(self):
        self.proj.build(self.project_folder, synth_only=True)

    def test_synth_should_fail_if_source_code_does_not_compile(self):
        with open(self.top_file, "a") as file_handle:
            file_handle.write("garbage\napa\nhest")

        with pytest.raises(CalledProcessError):
            self.proj.build(self.project_folder, synth_only=True)
        assert file_contains_string(self.log_file, "\nERROR: Run synth_1 failed.")

    def test_synth_with_unhandled_clock_crossing_should_fail(self):
        top = self.top_template.format(assign_output=self.unhandled_clock_crossing)
        create_file(self.top_file, top)

        with pytest.raises(CalledProcessError):
            self.proj.build(self.project_folder, synth_only=True)
        assert file_contains_string(self.log_file, "\nERROR: Unhandled clock crossing in synth_1 run.")

    def test_build_project(self):
        self.proj.build(self.project_folder, self.project_folder)
        assert exists(join(self.project_folder, self.proj.name + ".bit"))
        assert exists(join(self.project_folder, self.proj.name + ".bin"))
