from os.path import dirname, join
import unittest
import pytest

from hdl_reuse.system_utils import create_file
from hdl_reuse.registers import load_json_file, from_json


THIS_DIR = dirname(__file__)


class TestRegisters(unittest.TestCase):

    module_name = "sensor"
    json_file = join(THIS_DIR, "sensor_regs.json")
    json_data = """\
{
  "conf": {
    "description": "Set configuration bits",
    "mode": "r_w",
    "bits": {
      "enable": "Enable things",
      "disable": ""
    }
  },
  "cmd": {
    "mode": "w"
  },
  "irq": {
    "description": "Interrupt register",
    "mode": "r_w",
    "bits": {
      "bad": "",
      "not_good": ""
    }
  }%s
}
"""

    def setUp(self):
        create_file(self.json_file, self.json_data % "")
        self.registers = from_json(self.module_name, self.json_file)

    def test_order_of_registers_and_bits(self):
        register_list = self.registers.register_list

        assert register_list.registers[0].name == "conf"
        assert register_list.registers[1].name == "cmd"
        assert register_list.registers[2].name == "irq"

        assert register_list.registers[0].bits[0].name == "enable"
        assert register_list.registers[0].bits[1].name == "disable"
        assert register_list.registers[1].bits == []
        assert register_list.registers[2].bits[0].name == "bad"
        assert register_list.registers[2].bits[1].name == "not_good"

    def test_load_nonexistent_json_file_should_raise_exception(self):
        filename = self.json_file + "apa"
        with pytest.raises(ValueError) as exception_info:
            load_json_file(self.json_file + "apa")
        assert str(exception_info.value) == f"Requested json file does not exist: {filename}"

    def test_load_dirty_json_file_should_raise_exception(self):
        data = self.json_data % "apa"
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            load_json_file(self.json_file)
        assert str(exception_info.value).startswith(f"Error while parsing JSON file {self.json_file}:\nExpecting ',' delimiter")

    def test_no_mode_field_should_raise_exception(self):
        extras = """,
  "apa": {
    "description": "w"
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Register apa in {self.json_file} does not have mode field"

    def test_two_registers_with_same_name_should_raise_exception(self):
        extras = """,
  "conf": {
    "mode": "w"
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Error while parsing JSON file {self.json_file}:\nDuplicate key conf"

    def test_two_bits_with_same_name_should_raise_exception(self):
        extras = """,
  "test_reg": {
    "mode": "w",
    "bits": {
      "test_bit": "Declaration 1",
      "test_bit": "Declaration 2"
    }
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Error while parsing JSON file {self.json_file}:\nDuplicate key test_bit"
