# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import copy
import toml

from tsfpga.system_utils import read_file
from .register_list import RegisterList
from .constant import Constant


def load_toml_file(toml_file):
    if not toml_file.exists():
        raise FileNotFoundError(f"Requested TOML file does not exist: {toml_file}")

    raw_toml = read_file(toml_file)
    try:
        return toml.loads(raw_toml)
    except toml.TomlDecodeError as exception_info:
        message = f"Error while parsing TOML file {toml_file}:\n{exception_info}"
        raise ValueError(message) from exception_info


def from_toml(module_name, toml_file, default_registers=None):
    parser = RegisterParser(
        module_name=module_name,
        source_definition_file=toml_file,
        default_registers=default_registers,
    )
    toml_data = load_toml_file(toml_file)

    return parser.parse(toml_data)


class RegisterParser:

    recognized_constant_items = {"value", "description"}
    recognized_register_items = {"mode", "default_value", "description", "bits"}
    recognized_register_array_items = {"array_length", "register"}

    def __init__(self, module_name, source_definition_file, default_registers):
        self._register_list = RegisterList(
            name=module_name, source_definition_file=source_definition_file
        )
        self._source_definition_file = source_definition_file

        self._default_register_names = []
        if default_registers is not None:
            # Perform deep copy of the mutable register objects
            self._register_list.register_objects = copy.deepcopy(default_registers)
            for register in default_registers:
                self._default_register_names.append(register.name)

        self._names_taken = set()

    def parse(self, register_data):
        if "constant" in register_data:
            for name, items in register_data["constant"].items():
                self._parse_constant(name, items)

        if "register" in register_data:
            for name, items in register_data["register"].items():
                self._parse_plain_register(name, items)

        if "register_array" in register_data:
            for name, items in register_data["register_array"].items():
                self._parse_register_array(name, items)

        return self._register_list

    def _parse_constant(self, name, items):
        constant = Constant(name=name, value=items["value"])

        for item_name, item_value in items.items():
            if item_name not in self.recognized_constant_items:
                message = (
                    f"Error while parsing constant {name} in {self._source_definition_file}: "
                    f"Unknown key {item_name}"
                )
                raise ValueError(message)

            if item_name == "description":
                constant.description = item_value

        self._register_list.constants.append(constant)

    def _parse_plain_register(self, name, items):
        if name in self._default_register_names:
            # Default registers can be "updated" in the sense that the user can use a custom
            # description and add whatever bits they use in the current module. They can not however
            # change the mode.
            register = self._register_list.get_register(name)
            if "mode" in items:
                message = (
                    f"Overloading register {name} in {self._source_definition_file}, "
                    "one can not change mode from default"
                )
                raise ValueError(message)
        else:
            # If it is a new register however the mode has to be specified.
            if "mode" not in items:
                raise ValueError(
                    f"Register {name} in {self._source_definition_file} does not have mode field"
                )
            register = self._register_list.append_register(name, items["mode"])

        for item_name, item_value in items.items():
            if item_name not in self.recognized_register_items:
                message = (
                    f"Error while parsing register {name} in {self._source_definition_file}: "
                    f"Unknown key {item_name}"
                )
                raise ValueError(message)
            if item_name == "default_value":
                register.default_value = item_value

            if item_name == "description":
                register.description = item_value

            if item_name == "bits":
                for bit_name, bit_description in item_value.items():
                    register.append_bit(bit_name, bit_description)

        self._names_taken.add(name)

    def _parse_register_array(self, name, items):
        if name in self._names_taken:
            message = f"Duplicate name {name} in {self._source_definition_file}"
            raise ValueError(message)
        if "array_length" not in items:
            message = (
                f"Register array {name} in {self._source_definition_file} does not have "
                "array_length attribute"
            )
            raise ValueError(message)

        for item_name in items:
            if item_name not in self.recognized_register_array_items:
                message = (
                    f"Error while parsing register array {name} in {self._source_definition_file}: "
                    f"Unknown key {item_name}"
                )
                raise ValueError(message)

        length = items["array_length"]
        register_array = self._register_list.append_register_array(name, length)

        for register_name, register_items in items["register"].items():
            if "mode" not in register_items:
                message = (
                    f"Register {register_name} within array {name} in "
                    f"{self._source_definition_file} does not have mode field"
                )
                raise ValueError(message)
            register = register_array.append_register(register_name, register_items["mode"])

            for register_item_name, register_item_value in register_items.items():
                if register_item_name not in self.recognized_register_items:
                    message = (
                        f"Error while parsing register {register_name} in array {name} in "
                        f"{self._source_definition_file}: Unknown key {register_item_name}"
                    )
                    raise ValueError(message)
                if register_item_name == "default_value":
                    register.default_value = register_item_value

                if register_item_name == "description":
                    register.description = register_item_value

                if register_item_name == "bits":
                    for bit_name, bit_description in register_item_value.items():
                        register.append_bit(bit_name, bit_description)
