# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import subprocess
import unittest

import pytest

import tsfpga
from tsfpga.system_utils import create_file, run_command
from tsfpga.registers.parser import from_toml


@pytest.mark.usefixtures("fixture_tmp_path")
class TestRegisterCompilation(unittest.TestCase):
    """
    Functional test: TOML -> registers -> Code generation -> compilation
    """

    tmp_path = None

    def setUp(self):
        self.working_dir = self.tmp_path
        self.include_dir = self.working_dir / "include"

        toml_file = tsfpga.TSFPGA_EXAMPLE_MODULES / "artyz7" / "regs_artyz7.toml"
        self.registers = from_toml("artyz7", toml_file)

        self.registers.add_constant("data_width", 24)
        self.registers.add_constant("decrement", -8)

    def test_compiling_c_header(self):
        main_file = self.working_dir / "main.c"
        main = """\
#include <assert.h>
#include <stdint.h>
#include "artyz7_regs.h"

int main()
{
  // Assert constants
  assert(ARTYZ7_DATA_WIDTH == 24);
  assert(ARTYZ7_DECREMENT == -8);

  // Assert that indexes are correct
  assert(ARTYZ7_PLAIN_DUMMY_REG_INDEX == 0);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_INDEX(0) == 1);
  assert(ARTYZ7_DUMMY_REGS_SETTINGS_INDEX(0) == 2);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_INDEX(1) == 3);
  assert(ARTYZ7_DUMMY_REGS_SETTINGS_INDEX(1) == 4);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_INDEX(2) == 5);
  assert(ARTYZ7_DUMMY_REGS_SETTINGS_INDEX(2) == 6);

  // Assert that addresses are correct
  assert(ARTYZ7_PLAIN_DUMMY_REG_ADDR == 0);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_ADDR(0) == 4);
  assert(ARTYZ7_DUMMY_REGS_SETTINGS_ADDR(0) == 8);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_ADDR(1) == 12);
  assert(ARTYZ7_DUMMY_REGS_SETTINGS_ADDR(1) == 16);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_ADDR(2) == 20);
  assert(ARTYZ7_DUMMY_REGS_SETTINGS_ADDR(2) == 24);
  // Last register
  assert(ARTYZ7_DUMMY_REGS_SETTINGS_ADDR(2) == 4 * (ARTYZ7_NUM_REGS - 1));

  // Assert bit indexes
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_ENABLE_BIT == 0);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_ENABLE == 1);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_DISABLE_BIT == 1);
  assert(ARTYZ7_DUMMY_REGS_CONFIGURATION_DISABLE == 2);

  // Assert positions within the generated type
  artyz7_regs_t regs;
  assert(sizeof(regs) == 4 * ARTYZ7_NUM_REGS);

  assert((void *)&regs == (void *)&regs.plain_dummy_reg);
  assert((void *)&regs + 4 == (void *)&regs.dummy_regs[0].configuration);
  assert((void *)&regs + 8 == (void *)&regs.dummy_regs[0].settings);
  assert((void *)&regs + 12 == (void *)&regs.dummy_regs[1].configuration);
  assert((void *)&regs + 16 == (void *)&regs.dummy_regs[1].settings);
  assert((void *)&regs + 20 == (void *)&regs.dummy_regs[2].configuration);
  assert((void *)&regs + 24 == (void *)&regs.dummy_regs[2].settings);

  // Some dummy code that uses the generated type
  regs.plain_dummy_reg = 0;
  regs.dummy_regs[0].configuration = ARTYZ7_DUMMY_REGS_CONFIGURATION_ENABLE;
  regs.dummy_regs[2].settings = (1 << ARTYZ7_DUMMY_REGS_CONFIGURATION_ENABLE_BIT);

  return 0;
}
"""
        create_file(main_file, main)
        self.registers.create_c_header(self.include_dir)

        executable = self.working_dir / "artyz7.o"
        cmd = ["gcc", main_file, f"-o{executable}", f"-I{self.include_dir}"]
        run_command(cmd)
        run_command([executable])

    def test_compiling_cpp(self):
        main_file = self.working_dir / "main.cpp"
        main = """\
#include <assert.h>

#include "include/artyz7.h"

int main()
{
  // Assert constants
  assert(fpga_regs::Artyz7::data_width == 24);
  assert(fpga_regs::Artyz7::decrement == -8);

  assert(fpga_regs::Artyz7::num_registers == 7);

  // Allocate memory and instantiate the register class
  uint32_t memory[fpga_regs::Artyz7::num_registers];
  volatile uint8_t *base_address = reinterpret_cast<volatile uint8_t *>(memory);
  fpga_regs::Artyz7 artyz7 = fpga_regs::Artyz7(base_address);

  // Set data and then check, according to the expected register addresses.
  // Data is a ramp 0-6.
  artyz7.set_plain_dummy_reg(0);
  artyz7.set_dummy_regs_configuration(0, 1);
  // dummy_regs_settings is read only, so set the value in the memory straight away
  memory[2] = 2;
  artyz7.set_dummy_regs_configuration(1, 3);
  memory[4] = 4;
  artyz7.set_dummy_regs_configuration(2, 5);
  memory[6] = 6;

  assert(artyz7.get_plain_dummy_reg() == 0);
  assert(memory[0] == 0);

  assert(artyz7.get_dummy_regs_configuration(0) == 1);
  assert(memory[1] == 1);

  assert(artyz7.get_dummy_regs_settings(0) == 2);
  assert(memory[2] == 2);

  assert(artyz7.get_dummy_regs_configuration(1) == 3);
  assert(memory[3] == 3);

  assert(artyz7.get_dummy_regs_settings(1) == 4);
  assert(memory[4] == 4);

  assert(artyz7.get_dummy_regs_configuration(2) == 5);
  assert(memory[5] == 5);

  assert(artyz7.get_dummy_regs_settings(2) == 6);
  assert(memory[6] == 6);

  // Assert bit indexes
  assert(fpga_regs::Artyz7::dummy_regs_configuration_enable == 1);
  assert(fpga_regs::Artyz7::dummy_regs_configuration_disable == 2);

  return 0;
}
"""
        create_file(main_file, main)
        self.registers.create_cpp_interface(self.include_dir)
        self.registers.create_cpp_header(self.include_dir)
        self.registers.create_cpp_implementation(self.working_dir)
        cpp_class_file = self.working_dir / "artyz7.cpp"

        executable = self.working_dir / "artyz7.o"
        cmd = ["g++", main_file, cpp_class_file, f"-o{executable}", f"-I{self.include_dir}"]
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

  // Index 3 is out of bounds (should be less than 3)
  artyz7.set_dummy_regs_configuration(3, 1337);

  return 0;
}
"""
        create_file(main_file, main)
        self.registers.create_cpp_interface(self.include_dir)
        self.registers.create_cpp_header(self.include_dir)
        self.registers.create_cpp_implementation(self.working_dir)
        cpp_class_file = self.working_dir / "artyz7.cpp"

        executable = self.working_dir / "artyz7.o"
        cmd = ["g++", main_file, cpp_class_file, f"-o{executable}", f"-I{self.include_dir}"]
        run_command(cmd)

        process = subprocess.Popen([executable], stderr=subprocess.PIPE)
        stderr = process.communicate()
        assert "Assertion `array_index < dummy_regs_array_length' failed" in str(stderr), stderr
