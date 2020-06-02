# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import copy
import unittest

import pytest

from tsfpga.system_utils import create_file
from tsfpga.register_list import from_json, load_json_file, RegisterList
from tsfpga.register_types import Register


def get_test_default_registers():
    registers = [
        Register("config", 0, "r_w", "Configuration register."),
    ]
    return registers


def test_deep_copy_of_registers_actually_copies_everything():
    registers = get_test_default_registers()
    for register in registers:
        if register.name == "config":
            config_register = register

    registers_copy = copy.deepcopy(registers)
    for register in registers_copy:
        if register.name == "config":
            config_register_copy = register

    config_register_copy.description = "Dummy"
    config_register_copy.bits.append("dummy object")

    assert config_register.description == "Configuration register."
    assert len(config_register.bits) == 0


def test_invalid_register_mode_should_raise_exception():
    registers = RegisterList(None, None)
    registers.append_register("test", "r_w")

    with pytest.raises(ValueError) as exception_info:
        registers.append_register("hest", "x")
    assert str(exception_info.value) == 'Invalid mode "x" for register "hest"'

    register_array = registers.append_register_array("array", 2)
    register_array.append_register("apa", "r")
    with pytest.raises(ValueError) as exception_info:
        register_array.append_register("zebra", "y")
    assert str(exception_info.value) == 'Invalid mode "y" for register "zebra"'


def test_header_constants():
    registers = RegisterList(None, None)
    registers.add_constant("test", 123)
    registers.add_constant("hest", 456)

    assert registers.constants[0].name == "test"
    assert registers.constants[0].value == 123
    assert registers.constants[1].name == "hest"
    assert registers.constants[1].value == 456


@pytest.mark.usefixtures("fixture_tmp_path")
class TestRegisterList(unittest.TestCase):

    tmp_path = None

    module_name = "sensor"
    json_data = """\
{
  "data": {
    "mode": "w",
    "default_value": 3
  },
  "irq": {
    "description": "Interrupt register",
    "mode": "r_w",
    "bits": {
      "bad": "Bad things happen",
      "not_good": ""
    }
  },
  "configuration": {
    "array_length": 3,
    "registers": {
      "input_settings": {
        "description": "Input configuration",
        "mode": "r_w",
        "default_value": 1,
        "bits": {
          "enable": "Enable things",
          "disable": ""
        }
      },
      "output_settings": {
        "mode": "w",
        "bits": {
          "enable": "",
          "disable": "Disable things"
        }
      }
    }
  }%s
}
"""

    def setUp(self):
        self.json_file = create_file(self.tmp_path / "sensor_regs.json", self.json_data % "")

    def test_order_of_registers_and_bits(self):
        registers = from_json(self.module_name, self.json_file).register_objects

        assert registers[0].name == "data"
        assert registers[0].mode == "w"
        assert registers[0].index == 0
        assert registers[0].description == ""
        assert registers[0].default_value == 3
        assert registers[0].bits == []

        assert registers[1].name == "irq"
        assert registers[1].mode == "r_w"
        assert registers[1].index == 1
        assert registers[1].description == "Interrupt register"
        assert registers[1].default_value == 0
        assert registers[1].bits[0].name == "bad"
        assert registers[1].bits[0].description == "Bad things happen"
        assert registers[1].bits[1].name == "not_good"
        assert registers[1].bits[1].description == ""

        assert registers[2].name == "configuration"
        assert registers[2].length == 3
        assert registers[2].index == 2 + 2 * 3 - 1
        assert len(registers[2].registers) == 2
        assert registers[2].registers[0].name == "input_settings"
        assert registers[2].registers[0].mode == "r_w"
        assert registers[2].registers[0].index == 0
        assert registers[2].registers[0].description == "Input configuration"
        assert registers[2].registers[0].default_value == 1
        assert registers[2].registers[0].bits[0].name == "enable"
        assert registers[2].registers[0].bits[0].description == "Enable things"
        assert registers[2].registers[0].bits[1].name == "disable"
        assert registers[2].registers[0].bits[1].description == ""
        assert registers[2].registers[1].name == "output_settings"
        assert registers[2].registers[1].mode == "w"
        assert registers[2].registers[1].index == 1
        assert registers[2].registers[1].description == ""
        assert registers[2].registers[1].default_value == 0
        assert registers[2].registers[1].bits[0].name == "enable"
        assert registers[2].registers[1].bits[0].description == ""
        assert registers[2].registers[1].bits[1].name == "disable"
        assert registers[2].registers[1].bits[1].description == "Disable things"

    def test_default_registers(self):
        default_registers = get_test_default_registers()
        num_default_registers = len(default_registers)
        json_registers = from_json(self.module_name, self.json_file, default_registers)

        # The registers from this test are appended at the end
        assert json_registers.get_register("data").index == num_default_registers
        assert json_registers.get_register("irq").index == num_default_registers + 1

    def test_load_nonexistent_json_file_should_raise_exception(self):
        file = self.json_file.with_name("apa.json")
        with pytest.raises(FileNotFoundError) as exception_info:
            load_json_file(file)
        assert str(exception_info.value) == f"Requested json file does not exist: {file}"

    def test_load_dirty_json_file_should_raise_exception(self):
        data = self.json_data % "apa"
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            load_json_file(self.json_file)
        assert str(exception_info.value).startswith(f"Error while parsing JSON file {self.json_file}:\nExpecting ',' delimiter")

    def test_plain_register_with_array_length_attribute_should_raise_exception(self):
        extras = """,
  "apa": {
    "mode": "r_w",
    "array_length": 4
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Plain register apa in {self.json_file} can not have array_length attribute"

    def test_register_array_but_no_array_length_attribute_should_raise_exception(self):
        extras = """,
  "apa": {
    "registers": {}
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Register array apa in {self.json_file} does not have array_length attribute"

    def test_register_in_array_with_no_mode_attribute_should_raise_exception(self):
        extras = """,
  "apa": {
    "array_length": 2,
    "registers": {
      "hest": {
        "description": "nothing"
      }
    }
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Register hest within array apa in {self.json_file} does not have mode field"

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
  "irq": {
    "mode": "w"
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Error while parsing JSON file {self.json_file}:\nDuplicate key irq"

    def test_register_with_same_name_as_register_array_should_raise_exception(self):
        extras = """,
  "configuration": {
    "mode": "w"
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Error while parsing JSON file {self.json_file}:\nDuplicate key configuration"

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
        json_registers = from_json(self.module_name, self.json_file, get_test_default_registers())

        assert json_registers.get_register("config").description == "apa"

    def test_changing_mode_of_default_register_should_raise_exception(self):
        extras = """,
  "config": {
    "mode": "w"
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file, get_test_default_registers())
        assert str(exception_info.value) == f"Overloading register config in {self.json_file}, one can not change mode from default"

    def test_unknown_register_field_should_raise_exception(self):
        extras = """,
  "test_reg": {
    "mode": "w",
    "dummy": 3
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Error while parsing register test_reg in {self.json_file}:\nUnknown key dummy"

    def test_unknown_register_array_field_should_raise_exception(self):
        extras = """,
  "test_array": {
    "array_length": 2,
    "dummy": 3,
    "registers": {
      "hest": {
        "mode": "r"
      }
    }
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Error while parsing register array test_array in {self.json_file}:\nUnknown key dummy"

    def test_unknown_register_field_in_register_array_should_raise_exception(self):
        extras = """,
  "test_array": {
    "array_length": 2,
    "registers": {
      "hest": {
        "mode": "r",
        "dummy": 3
      }
    }
  }"""
        data = self.json_data % extras
        create_file(self.json_file, data)

        with pytest.raises(ValueError) as exception_info:
            from_json(self.module_name, self.json_file)
        assert str(exception_info.value) == f"Error while parsing register hest in array test_array in {self.json_file}:\nUnknown key dummy"
