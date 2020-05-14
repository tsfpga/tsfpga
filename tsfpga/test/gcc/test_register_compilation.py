# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import subprocess
import unittest

import pytest

import tsfpga
from tsfpga.system_utils import create_file, run_command
from tsfpga.register_list import from_json


@pytest.mark.usefixtures("fixture_tmp_path")
class TestRegisterCompilation(unittest.TestCase):
    """
    Functional test: JSON -> registers -> Code generation -> compilation
    """

    tmp_path = None

    def setUp(self):
        self.working_dir = self.tmp_path
        self.include_dir = self.working_dir / "include"

        json_file = tsfpga.TSFPGA_EXAMPLE_MODULES / "artyz7" / "regs_artyz7.json"
        self.registers = from_json("artyz7", json_file)

        self.registers.add_constant("data_width", 24)
        self.registers.add_constant("decrement", -8)

    def test_compiling_c_header(self):
        main_file = self.working_dir / "main.c"
        main = """\
#include "artyz7_regs.h"
#include <assert.h>

int main()
{
  artyz7_regs_t regs;

  assert(sizeof(regs) == 4 * ARTYZ7_NUM_REGS);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_ADDR(3) == ARTYZ7_DUMMY_REGS_SETTINGS_ADDR(3) - 4);
  assert(ARTYZ7_DUMMY_REGS_SETTINGS_ADDR(3) == ARTYZ7_PLAIN_DUMMY_REG_ADDR - 4);
  assert(ARTYZ7_PLAIN_DUMMY_REG_ADDR == 4 * (ARTYZ7_NUM_REGS - 1));

  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_ENABLE_BIT == 0);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_ENABLE == 1);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_DISABLE_BIT == 1);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_DISABLE == 2);

  regs.plain_dummy_reg = 0;
  regs.dummy_regs[0].configuration = ARTYZ7_DUMMY_REGS_CONFIGURATION_ENABLE;
  regs.dummy_regs[3].settings = (1 << ARTYZ7_DUMMY_REGS_CONFIGURATION_ENABLE_BIT);

  assert(ARTYZ7_CONSTANT_DATA_WIDTH == 24);
  assert(ARTYZ7_CONSTANT_DECREMENT == -8);

  return 0;
}
"""
        create_file(main_file, main)
        self.registers.create_c_header(self.include_dir)

        executable = self.working_dir / "artyz7.o"
        cmd = [
            "gcc",
            main_file,
            f"-o{executable}",
            f"-I{self.include_dir}"
        ]
        run_command(cmd)
        run_command([executable])

    def test_compiling_cpp(self):
        main_file = self.working_dir / "main.cpp"
        main = """\
#include <assert.h>

#include "include/artyz7.h"

int main()
{
  uint32_t data[fpga_regs::Artyz7::num_registers];
  volatile uint8_t *base_address = reinterpret_cast<volatile uint8_t *>(data);
  fpga_regs::Artyz7 artyz7 = fpga_regs::Artyz7(base_address);

  artyz7.set_plain_dummy_reg(1337);
  artyz7.set_dummy_regs_configuration(2, 0xfeed);
  artyz7.set_dummy_regs_settings(3, 0);
  artyz7.set_dummy_regs_configuration(3, fpga_regs::Artyz7::dummy_regs_configuration_enable);

  assert(artyz7.get_plain_dummy_reg() == 1337);
  assert(artyz7.get_dummy_regs_configuration(2) == 0xfeed);
  assert(artyz7.get_dummy_regs_settings(3) == 0);
  assert(artyz7.get_dummy_regs_configuration(3) == fpga_regs::Artyz7::dummy_regs_configuration_enable);

  assert(fpga_regs::Artyz7::dummy_regs_configuration_enable == 1);
  assert(fpga_regs::Artyz7::dummy_regs_configuration_disable == 2);

  assert(fpga_regs::Artyz7::data_width == 24);
  assert(fpga_regs::Artyz7::decrement == -8);

  return 0;
}
"""
        create_file(main_file, main)
        self.registers.create_cpp_interface(self.include_dir)
        self.registers.create_cpp_header(self.include_dir)
        self.registers.create_cpp_implementation(self.working_dir)
        cpp_class_file = self.working_dir / "artyz7.cpp"

        executable = self.working_dir / "artyz7.o"
        cmd = [
            "g++",
            main_file,
            cpp_class_file,
            f"-o{executable}",
            f"-I{self.include_dir}"
        ]
        run_command(cmd)
        run_command([executable])

    def test_setting_cpp_register_array_out_of_bounds_should_crash(self):
        main_file = self.working_dir / "main.cpp"
        main = """\
#include <assert.h>

#include "include/artyz7.h"

int main()
{
  uint32_t data[fpga_regs::Artyz7::num_registers];
  volatile uint8_t *base_address = reinterpret_cast<volatile uint8_t *>(data);
  fpga_regs::Artyz7 artyz7 = fpga_regs::Artyz7(base_address);

  artyz7.set_dummy_regs_settings(4, 1337);

  return 0;
}
"""
        create_file(main_file, main)
        self.registers.create_cpp_interface(self.include_dir)
        self.registers.create_cpp_header(self.include_dir)
        self.registers.create_cpp_implementation(self.working_dir)
        cpp_class_file = self.working_dir / "artyz7.cpp"

        executable = self.working_dir / "artyz7.o"
        cmd = [
            "g++",
            main_file,
            cpp_class_file,
            f"-o{executable}",
            f"-I{self.include_dir}"
        ]
        run_command(cmd)

        process = subprocess.Popen([executable], stderr=subprocess.PIPE)
        stderr = process.communicate()
        assert "Assertion `array_index < dummy_regs_array_length' failed" in str(stderr), stderr
