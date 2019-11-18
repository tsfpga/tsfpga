# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import copy
from os.path import dirname, join
import unittest
import pytest

from tsfpga.system_utils import create_file
from tsfpga.registers import load_json_file, from_json, get_default_registers


THIS_DIR = dirname(__file__)


def test_deep_copy_of_register_actually_copies_everything():
    registers = get_default_registers()
    registers_copy = copy.deepcopy(registers)

    registers_copy["config"].description = "Dummy"
    registers_copy["config"].bits.append("dummy object")

    assert registers["config"].description == "Configuration register."
    assert len(registers["config"].bits) == 0


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

    def test_order_of_registers_and_bits(self):
        json_registers = from_json(self.module_name, self.json_file)
        registers = list(json_registers.register_list.registers.values())

        assert registers[0].name == "conf"
        assert registers[1].name == "cmd"
        assert registers[2].name == "irq"

        assert registers[0].bits[0].name == "enable"
        assert registers[0].bits[1].name == "disable"
        assert registers[1].bits == []
        assert registers[2].bits[0].name == "bad"
        assert registers[2].bits[1].name == "not_good"

    def test_default_registers(self):
        default_registers = get_default_registers()
        num_default_registers = len(default_registers)
        json_registers = from_json(self.module_name, self.json_file, default_registers)

        # The registers from this test are appended at the end
        assert json_registers.register_list.registers["conf"].idx == num_default_registers
        assert json_registers.register_list.registers["cmd"].idx == num_default_registers + 1
        assert json_registers.register_list.registers["irq"].idx == num_default_registers + 2

    def test_load_nonexistent_json_file_should_raise_exception(self):
        filename = self.json_file + "apa"
        with pytest.raises(FileNotFoundError) as exception_info:
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

    def test_overriding_default_register(self):
        extras = """,
  "config": {
    "description": "apa"
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)
        json_registers = from_json(self.module_name, self.json_file, get_default_registers())

        assert json_registers.register_list.registers["config"].description == "apa"

    def test_changing_mode_of_default_register_should_raise_exception(self):
        extras = """,
  "config": {
    "mode": "w"
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file, get_default_registers())
        assert str(exception_info.value) == f"Overloading register config in {self.json_file}, one can not change mode from default"
