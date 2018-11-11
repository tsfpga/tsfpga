from os.path import dirname, join, abspath
import unittest

from hdl_reuse.system_utils import create_file, run_command
from hdl_reuse.registers import from_json


THIS_DIR = dirname(__file__)


class TestRegisterCCompilation(unittest.TestCase):

    working_dir = abspath(join(THIS_DIR, "compilation"))

    module_name = "sensor"
    json_file = join(working_dir, "sensor_regs.json")
    json_data = """\
{
  "conf": {
    "mode": "r_w",
    "bits": {
      "enable": "",
      "disable": ""
    }
  },
  "irq": {
    "mode": "r_w",
    "bits": {
      "bad": "",
      "not_good": ""
    }
  }
}
"""

    c_main_file = join(working_dir, "main.c")
    c_main = """\
#include "sensor_regs.h"

int main() {
  struct sensor_regs_t regs;
  regs.conf = SENSOR_CONF_ENABLE;
  regs.irq = (1 << SENSOR_IRQ_BAD_BIT);
  return 0;
}
"""

    def test_compiling_c_header(self):
        """
        Functional test: JSON -> registers -> C header -> compilation
        """
        create_file(self.json_file, self.json_data)
        registers = from_json(self.module_name, self.json_file)
        registers.create_c_header(join(self.working_dir, "header"))

        create_file(self.c_main_file, self.c_main)

        cmd = [
            "gcc",
            self.c_main_file,
            "-o" + join(self.working_dir, "sensor.o"),
            "-I" + join(self.working_dir, "header")
        ]
        run_command(cmd)
