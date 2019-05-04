# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from os.path import dirname, join, abspath
import unittest

from tsfpga.system_utils import create_file, delete, run_command
from tsfpga.registers import from_json


THIS_DIR = dirname(__file__)


class TestRegisterCompilation(unittest.TestCase):
    """
    Functional test: JSON -> registers -> Code generation -> compilation
    """

    working_dir = abspath(join(THIS_DIR, "compilation"))
    include_dir = join(working_dir, "include")

    def setUp(self):
        delete(self.working_dir)
        module_name = "sensor"
        json_file = join(self.working_dir, "sensor_regs.json")
        json_data = """\
{
  "config": {
    "mode": "r_w",
    "bits": {
      "enable": "",
      "disable": ""
    }
  },
  "irq_status": {
    "mode": "r_w",
    "bits": {
      "bad": "",
      "not_good": ""
    }
  }
}
"""

        create_file(json_file, json_data)
        self.registers = from_json(module_name, json_file)

    def test_compiling_c_header(self):
        main_file = join(self.working_dir, "main.c")
        main = """\
#include "sensor_regs.h"

int main()
{
  struct sensor_regs_t regs;
  regs.config = SENSOR_CONFIG_ENABLE;
  regs.irq_status = (1 << SENSOR_IRQ_STATUS_BAD_BIT);
  return 0;
}
"""
        create_file(main_file, main)
        self.registers.create_c_header(self.include_dir)

        executable = join(self.working_dir, "sensor.o")
        cmd = [
            "gcc",
            main_file,
            "-o" + executable,
            "-I" + self.include_dir
        ]
        run_command(cmd)
        run_command([executable])

    def test_compiling_cpp(self):
        main_file = join(self.working_dir, "main.cpp")
        main = """\
#include <assert.h>

#include "include/sensor.h"

int main()
{
  long long data;
  volatile uint8_t *base_address = reinterpret_cast<volatile uint8_t *>(&data);
  fpga_regs::Sensor sensor = fpga_regs::Sensor(base_address);

  sensor.set_config(1337);
  sensor.set_irq_status(666);
  assert(sensor.get_config() == 1337);
  assert(sensor.get_irq_status() == 666);

  return 0;
}
"""
        create_file(main_file, main)
        self.registers.create_cpp_interface(self.include_dir)
        self.registers.create_cpp_header(self.include_dir)
        self.registers.create_cpp_implementation(self.working_dir)
        cpp_class_file = join(self.working_dir, "sensor.cpp")

        executable = join(self.working_dir, "sensor.o")
        cmd = [
            "g++",
            main_file,
            cpp_class_file,
            "-o" + executable,
            "-I" + self.working_dir
        ]
        run_command(cmd)
        run_command([executable])
