from os.path import dirname, join
import unittest

from hdl_reuse.module import get_modules
from hdl_reuse.test.test_utils import create_file, delete
from hdl_reuse.vivado_project import VivadoProject


THIS_DIR = dirname(__file__)


class TestBasicProject(unittest.TestCase):

    part = "xczu3eg-sfva625-1-i"
    project_folder = join(THIS_DIR, "vivado")
    modules_folder = join(THIS_DIR, "modules")

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
begin
  output <= not input;
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
"""

    def setUp(self):
        delete(self.modules_folder)  # These should probably be in tearDown()
        delete(self.project_folder)  # But we keep them here som we can manually open and examine the project in Vivado

        create_file(self.top_file, self.top)
        create_file(self.constraint_file, self.constraints)

        self.modules = get_modules([self.modules_folder])

    def test_create_a_basic_project(self):
        proj = VivadoProject(name="test_proj", modules=self.modules, part=self.part, vivado_path="vivado", constraints=[self.constraint_file])
        proj.create(self.project_folder)
