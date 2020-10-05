# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import copy
import unittest
from unittest.mock import patch
from pathlib import Path
import pytest

from tsfpga.system_utils import create_file
from tsfpga.registers.register_list import from_toml, load_toml_file, RegisterList
from tsfpga.registers.register import Register


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
    constant_test = registers.add_constant("test", 123)
    registers.add_constant("hest", 456, "hest is best!")

    assert len(registers.constants) == 2

    assert registers.get_constant("test").name == "test"
    assert registers.get_constant("test").value == 123
    assert registers.get_constant("test").description == ""

    assert registers.get_constant("hest").name == "hest"
    assert registers.get_constant("hest").value == 456
    assert registers.get_constant("hest").description == "hest is best!"

    assert registers.get_constant("apa") is None

    constant_test.value = -5
    assert registers.get_constant("test").value == -5


def test_registers_are_appended_properly_and_can_be_edited_in_place():
    register_array = RegisterList(name="apa", source_definition_file=Path("."))

    register_hest = register_array.append_register(name="hest", mode="r")
    assert register_hest.index == 0

    register_zebra = register_array.append_register(name="zebra", mode="r")
    assert register_zebra.index == 1

    register_hest.description = "new desc"
    assert register_array.register_objects[0].description == "new desc"


def test_register_arrays_are_appended_properly_and_can_be_edited_in_place():
    register_array = RegisterList(name="apa", source_definition_file=Path("."))

    register_array_hest = register_array.append_register_array(name="hest", length=4)
    assert register_array_hest.base_index == 0
    register_array_hest.append_register(name="foo", mode="r")
    register_array_hest.append_register(name="bar", mode="w")

    register_array_zebra = register_array.append_register_array(name="zebra", length=2)
    assert register_array_zebra.base_index == 8


def test_repr_basic():
    # Check that repr is an actual representation, not just "X object at 0xABCDEF"
    assert "apa" in repr(RegisterList(name="apa", source_definition_file=Path(".")))

    # Different name
    assert repr(RegisterList(name="apa", source_definition_file=Path("."))) != repr(
        RegisterList(name="hest", source_definition_file=Path("."))
    )

    # Different source_definition_file
    assert repr(RegisterList(name="apa", source_definition_file=Path("."))) != repr(
        RegisterList(name="apa", source_definition_file=Path("./zebra"))
    )


def test_repr_with_constant_added():
    register_list_a = RegisterList(name="apa", source_definition_file=Path("."))
    register_list_b = RegisterList(name="apa", source_definition_file=Path("."))
    assert repr(register_list_a) == repr(register_list_b)

    register_list_a.add_constant(name="zebra", value=3)

    assert repr(register_list_a) != repr(register_list_b)


def test_repr_with_register_appended():
    register_list_a = RegisterList(name="apa", source_definition_file=Path("."))
    register_list_b = RegisterList(name="apa", source_definition_file=Path("."))
    assert repr(register_list_a) == repr(register_list_b)

    register_list_a.append_register(name="zebra", mode="w")

    assert repr(register_list_a) != repr(register_list_b)


def test_repr_with_register_array_appended():
    register_list_a = RegisterList(name="apa", source_definition_file=Path("."))
    register_list_b = RegisterList(name="apa", source_definition_file=Path("."))
    assert repr(register_list_a) == repr(register_list_b)

    register_list_a.append_register_array(name="zebra", length=4)

    assert repr(register_list_a) != repr(register_list_b)


# pylint: disable=too-many-public-methods
@pytest.mark.usefixtures("fixture_tmp_path")
class TestRegisterList(unittest.TestCase):

    tmp_path = None

    module_name = "sensor"
    toml_data = """\

################################################################################
[register.data]

mode = "w"
default_value = 3


################################################################################
[register.irq]

mode = "r_w"
description = "Interrupt register"

[register.irq.bits]

bad = "Bad things happen"
not_good = ""


################################################################################
[register_array.configuration]

array_length = 3

# ------------------------------------------------------------------------------
[register_array.configuration.register.input_settings]

description = "Input configuration"
mode = "r_w"
default_value = 1

[register_array.configuration.register.input_settings.bits]

enable = "Enable things"
disable = ""


# ------------------------------------------------------------------------------
[register_array.configuration.register.output_settings]

mode = "w"

[register_array.configuration.register.output_settings.bits]

enable = ""
disable = "Disable things"


################################################################################
%s
"""

    def setUp(self):
        self.toml_file = create_file(self.tmp_path / "sensor_regs.toml", self.toml_data % "")

    def create_toml_file_with_extras(self, toml_extras):
        data = self.toml_data % toml_extras
        create_file(self.toml_file, data)

    def test_order_of_registers_and_bits(self):
        registers = from_toml(self.module_name, self.toml_file).register_objects

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
        toml_registers = from_toml(self.module_name, self.toml_file, default_registers)

        # The registers from this test are appended at the end
        assert toml_registers.get_register("data").index == num_default_registers
        assert toml_registers.get_register("irq").index == num_default_registers + 1

    def test_load_nonexistent_toml_file_should_raise_exception(self):
        file = self.toml_file.with_name("apa.toml")
        with pytest.raises(FileNotFoundError) as exception_info:
            load_toml_file(file)
        assert str(exception_info.value) == f"Requested TOML file does not exist: {file}"

    def test_load_dirty_toml_file_should_raise_exception(self):
        self.create_toml_file_with_extras("apa")

        with pytest.raises(ValueError) as exception_info:
            load_toml_file(self.toml_file)
        assert str(exception_info.value).startswith(
            f"Error while parsing TOML file {self.toml_file}:\nKey name found without value."
        )

    def test_plain_register_with_array_length_attribute_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register.apa]

mode = "r_w"
array_length = 4
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert (
            str(exception_info.value)
            == f"Plain register apa in {self.toml_file} can not have array_length attribute"
        )

    def test_register_array_but_no_array_length_attribute_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register_array.apa]

[register_array.apa.register.hest]

mode = "r_w"
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert (
            str(exception_info.value)
            == f"Register array apa in {self.toml_file} does not have array_length attribute"
        )

    def test_register_in_array_with_no_mode_attribute_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register_array.apa]

array_length = 2

[register_array.apa.register.hest]

description = "nothing"
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert (
            str(exception_info.value)
            == f"Register hest within array apa in {self.toml_file} does not have mode field"
        )

    def test_no_mode_field_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register.apa]

description = "w"
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert (
            str(exception_info.value)
            == f"Register apa in {self.toml_file} does not have mode field"
        )

    def test_two_registers_with_same_name_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register.irq]

mode = "w"
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert str(exception_info.value).startswith(
            f"Error while parsing TOML file {self.toml_file}:\nWhat? irq already exists?"
        )

    def test_register_with_same_name_as_register_array_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register.configuration]

mode = "w"
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert str(exception_info.value) == f"Duplicate name configuration in {self.toml_file}"

    def test_two_bits_with_same_name_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register.test_reg]

mode = "w"

[register.test_reg.bits]

test_bit = "Declaration 1"
test_bit = "Declaration 2"
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert str(exception_info.value).startswith(
            f"Error while parsing TOML file {self.toml_file}:\nDuplicate keys!"
        )

    def test_overriding_default_register(self):
        self.create_toml_file_with_extras(
            """
[register.config]

description = "apa"
"""
        )
        toml_registers = from_toml(self.module_name, self.toml_file, get_test_default_registers())

        assert toml_registers.get_register("config").description == "apa"

    def test_changing_mode_of_default_register_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register.config]

mode = "w"
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file, get_test_default_registers())
        assert (
            str(exception_info.value)
            == f"Overloading register config in {self.toml_file}, one can not change mode "
            "from default"
        )

    def test_unknown_register_field_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register.test_reg]

mode = "w"
dummy = 3
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert (
            str(exception_info.value)
            == f"Error while parsing register test_reg in {self.toml_file}:\nUnknown key dummy"
        )

    def test_unknown_register_array_field_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register_array.test_array]

array_length = 2
dummy = 3

[register_array.test_array.hest]

mode = "r"
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert (
            str(exception_info.value)
            == f"Error while parsing register array test_array in {self.toml_file}:\n"
            "Unknown key dummy"
        )

    def test_unknown_register_field_in_register_array_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[register_array.test_array]

array_length = 2

[register_array.test_array.register.hest]

mode = "r"
dummy = 3
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert (
            str(exception_info.value)
            == f"Error while parsing register hest in array test_array in {self.toml_file}:\n"
            "Unknown key dummy"
        )

    def test_constants_in_toml(self):
        self.create_toml_file_with_extras(
            """
[constant.data_width]

value = 0xf
description = "the width"
"""
        )

        register_list = from_toml(self.module_name, self.toml_file)
        assert len(register_list.constants) == 1
        assert register_list.constants[0].name == "data_width"
        assert register_list.constants[0].value == 15
        assert register_list.constants[0].description == "the width"

    def test_unknown_constant_field_should_raise_exception(self):
        self.create_toml_file_with_extras(
            """
[constant.data_width]

value = 0xf
default_value = 0xf
"""
        )

        with pytest.raises(ValueError) as exception_info:
            from_toml(self.module_name, self.toml_file)
        assert (
            str(exception_info.value)
            == f"Error while parsing constant data_width in {self.toml_file}:\n"
            "Unknown key default_value"
        )

    def test_create_vhdl_package_should_not_run_again_if_nothing_has_changed(self):
        register_list = from_toml(self.module_name, self.toml_file)
        register_list.add_constant(name="apa", value=3)
        register_list.create_vhdl_package(self.tmp_path)

        register_list = from_toml(self.module_name, self.toml_file)
        register_list.add_constant(name="apa", value=3)
        with patch(
            "tsfpga.registers.register_list.RegisterList._create_vhdl_package", autospec=True
        ) as mocked_create_vhdl_package:
            register_list.create_vhdl_package(self.tmp_path)
            mocked_create_vhdl_package.assert_not_called()

    def test_create_vhdl_package_should_run_again_if_file_has_changed(self):
        register_list = from_toml(self.module_name, self.toml_file)
        register_list.create_vhdl_package(self.tmp_path)

        self.create_toml_file_with_extras(
            """
[constant.apa]

value = 3
"""
        )
        register_list = from_toml(self.module_name, self.toml_file)
        with patch(
            "tsfpga.registers.register_list.RegisterList._create_vhdl_package", autospec=True
        ) as mocked_create_vhdl_package:
            register_list.create_vhdl_package(self.tmp_path)
            mocked_create_vhdl_package.assert_called_once()

    def test_create_vhdl_package_should_run_again_if_list_is_modified(self):
        register_list = from_toml(self.module_name, self.toml_file)
        register_list.create_vhdl_package(self.tmp_path)

        register_list = from_toml(self.module_name, self.toml_file)
        register_list.add_constant(name="apa", value=3)
        with patch(
            "tsfpga.registers.register_list.RegisterList._create_vhdl_package", autospec=True
        ) as mocked_create_vhdl_package:
            register_list.create_vhdl_package(self.tmp_path)
            mocked_create_vhdl_package.assert_called_once()

    def test_create_vhdl_package_should_run_again_if_hash_can_not_be_read(self):
        register_list = from_toml(self.module_name, self.toml_file)
        register_list.create_vhdl_package(self.tmp_path)

        # Overwrite the generated file
        vhd_file = self.tmp_path / "sensor_regs_pkg.vhd"
        assert vhd_file.exists()
        create_file(vhd_file, contents="-- Mumbo jumbo\n")

        register_list = from_toml(self.module_name, self.toml_file)
        with patch(
            "tsfpga.registers.register_list.RegisterList._create_vhdl_package", autospec=True
        ) as mocked_create_vhdl_package:
            register_list.create_vhdl_package(self.tmp_path)
            mocked_create_vhdl_package.assert_called_once()
