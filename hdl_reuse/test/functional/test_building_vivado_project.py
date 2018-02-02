from os.path import dirname, join
import pytest
from subprocess import CalledProcessError
import unittest

from hdl_reuse.module import get_modules
from hdl_reuse.test.test_utils import create_file, delete
from hdl_reuse.vivado_project import VivadoProject


THIS_DIR = dirname(__file__)


class TestBasicProject(unittest.TestCase):

    part = "xczu3eg-sfva625-1-i"
    modules_folder = join(THIS_DIR, "modules")
    project_folder = join(THIS_DIR, "vivado")

    top_file = join(modules_folder, "apa", "test_proj_top.vhd")
    top = """
library ieee;
use ieee.std_logic_1164.all;

entity test_proj_top is
  port (
    clk_1 : in std_logic;
    clk_2 : in std_logic;
    input : in std_logic;
    output : out std_logic
  );
end entity;

architecture a of test_proj_top is
  signal input_p1, input_p2 : std_logic;
begin

  assign_output : process
  begin
    wait until rising_edge(clk_1);
    output <= input_p2;
   end process;

  pipe_input : process
  begin
    wait until rising_edge(clk_2);
    input_p2 <= input_p1;
    input_p1 <= input;
  end process;

end architecture;
"""

    constraint_file = join(modules_folder, "apa", "test_proj.tcl")
    constraints = """
set_property package_pin Y5 [get_ports clk_1]
set_property package_pin W6 [get_ports clk_2]
set_property package_pin W7 [get_ports input]
set_property package_pin W8 [get_ports output]

set_property iostandard lvcmos18 [get_ports clk_1]
set_property iostandard lvcmos18 [get_ports clk_2]
set_property iostandard lvcmos18 [get_ports input]
set_property iostandard lvcmos18 [get_ports output]

# 200 MHz
create_clock -period 5 -name clk_1 [get_ports clk_1]
create_clock -period 5 -name clk_2 [get_ports clk_2]
"""

    def setUp(self):
        create_file(self.top_file, self.top)
        create_file(self.constraint_file, self.constraints)

        self.modules = get_modules([self.modules_folder])

    def tearDown(self):
        delete(self.modules_folder)
        delete(self.project_folder)

    def test_create_project(self):
        proj = VivadoProject(name="test_create_proj", modules=self.modules, part=self.part, constraints=[self.constraint_file])
        proj.create(self.project_folder)

    def test_synth_project(self):
        proj = VivadoProject(name="test_synth_project", modules=self.modules, part=self.part, constraints=[self.constraint_file])
        proj.create(self.project_folder)
        proj.build(self.project_folder, synth_only=True)

    def test_synth_should_raise_exception_if_source_code_does_not_compile(self):
        with open(self.top_file, "a") as file_handle:
            file_handle.write("garbage\napa\nhest")

        proj = VivadoProject(name="test_build_project", modules=self.modules, part=self.part, constraints=[self.constraint_file])
        proj.create(self.project_folder)
        with pytest.raises(CalledProcessError):
            proj.build(self.project_folder, synth_only=True)

    def test_build_project(self):
        proj = VivadoProject(name="test_build_project", modules=self.modules, part=self.part, constraints=[self.constraint_file])
        proj.create(self.project_folder)
        proj.build(self.project_folder, self.project_folder)
