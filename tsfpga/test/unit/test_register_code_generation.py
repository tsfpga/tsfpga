# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import unittest

from tsfpga.register_c_generator import RegisterCGenerator
from tsfpga.register_cpp_generator import RegisterCppGenerator
from tsfpga.register_html_generator import RegisterHtmlGenerator
from tsfpga.register_list import RegisterList
from tsfpga.register_vhdl_generator import RegisterVhdlGenerator


class TestRegisterCodeGeneration(unittest.TestCase):

    def setUp(self):
        self.register_list = RegisterList("sensor")

        register = self.register_list.append("conf", "r_w")
        register.description = "conf desc"
        register.append_bit("bit_0", "conf bit 0 desc")
        register.append_bit("bit_1", "")

        register = self.register_list.append("addr", "w")
        register.description = "addr desc is _very_ good"

    def test_generated_html_contains_all_fields_in_correct_order(self):
        expected = """
  <tr>
    <td><strong>conf</strong></td>
    <td>0x0000</td>
    <td>Read, Write</td>
    <td>conf desc</td>
  </tr>
  <tr>
    <td>&nbsp;&nbsp;<em>bit_0</em></td>
    <td>0</td>
    <td></td>
    <td>conf bit 0 desc</td>
  </tr>
  <tr>
    <td>&nbsp;&nbsp;<em>bit_1</em></td>
    <td>1</td>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td><strong>addr</strong></td>
    <td>0x0004</td>
    <td>Write</td>
    <td>addr desc is <em>very</em> good</td>
  </tr>
"""
        html_generator = RegisterHtmlGenerator(self.register_list)
        assert expected in html_generator.get_table()
        assert expected in html_generator.get_page()

    def test_generated_vhdl_contains_all_fields_in_correct_order(self):
        vhdl_generator = RegisterVhdlGenerator(self.register_list)
        expected = """
  constant sensor_conf : integer := 0;
  constant sensor_addr : integer := 1;
"""
        assert expected in vhdl_generator.get_package()
        expected = """
    (idx => sensor_conf, reg_type => r_w),
    (idx => sensor_addr, reg_type => w)
"""
        assert expected in vhdl_generator.get_package()
        expected = """
  constant sensor_conf_bit_0 : integer := 0;
  constant sensor_conf_bit_1 : integer := 1;
"""
        assert expected in vhdl_generator.get_package()

    def test_generated_c_contains_all_fields_in_correct_order(self):
        c_generator = RegisterCGenerator(self.register_list)
        expected = """
struct sensor_regs_t {
  uint32_t conf;
  uint32_t addr;
};
"""
        assert expected in c_generator.get_header()

        expected = """
#define SENSOR_CONF_BIT_0_BIT (0uL)
#define SENSOR_CONF_BIT_0     (1uL)

#define SENSOR_CONF_BIT_1_BIT (1uL)
#define SENSOR_CONF_BIT_1     (2uL)
"""
        assert expected in c_generator.get_header()

    def test_generated_cpp_contains_all_fields_in_correct_order(self):
        cpp_generator = RegisterCppGenerator(self.register_list)
        expected = """
  static const uint32_t conf_bit_0 = 1uL;
  static const uint32_t conf_bit_1 = 2uL;
"""
        assert expected in cpp_generator.get_interface()

        expected = """
uint32_t Sensor::get_conf() const
{
  return m_registers[0];
}

void Sensor::set_conf(uint32_t value) const
{
  m_registers[0] = value;
}

void Sensor::set_addr(uint32_t value) const
{
  m_registers[1] = value;
}
"""
        assert expected in cpp_generator.get_implementation()

        # Write-only register should not have getter method
        assert "get_addr" not in cpp_generator.get_implementation()
