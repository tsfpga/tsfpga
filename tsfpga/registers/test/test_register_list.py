# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import unittest
from unittest.mock import patch
from pathlib import Path
import pytest

from tsfpga.system_utils import create_file
from tsfpga.registers.parser import from_toml
from tsfpga.registers.register import Register
from tsfpga.registers.register_list import RegisterList


def get_test_default_registers():
    registers = [
        Register("config", 0, "r_w", "Configuration register."),
    ]
    return registers


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

"""

    def setUp(self):
        self.toml_file = self.create_toml_file_with_extras()

    def create_toml_file_with_extras(self, toml_extras=""):
        data = self.toml_data + toml_extras
        return create_file(self.tmp_path / "sensor_regs.toml", data)

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
