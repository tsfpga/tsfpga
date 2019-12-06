# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from collections import OrderedDict
import json
from os.path import join

from tsfpga.register_c_generator import RegisterCGenerator
from tsfpga.register_cpp_generator import RegisterCppGenerator
from tsfpga.register_html_generator import RegisterHtmlGenerator
from tsfpga.register_list import RegisterList, Register
from tsfpga.register_vhdl_generator import RegisterVhdlGenerator
from tsfpga.system_utils import create_file


def get_default_registers():
    registers = OrderedDict(
        config=Register("config", 0, "r_w", "Configuration register."),
        command=Register(
            "command", 1, "wpulse",
            "When this register is written, all '1's in the written word will be asserted for one "
            "clock cycle in the FPGA logic."),
        status=Register("status", 2, "r", "Status register."),
        irq_status=Register(
            "irq_status", 3, "r_wpulse",
            "Reading a '1' in this register means the corresponding interrupt has triggered. Writing "
            "to this register will clear the interrupts where there is a '1' in the written word."),
        irq_mask=Register(
            "irq_mask", 4, "r_w",
            "A '1' in this register means that the corresponding interrupt is enabled. ")
    )
    return registers


class Registers:

    def __init__(self, register_list):
        self.register_list = register_list

    def create_vhdl_package(self, output_path):
        """
        Assumes that the output_path folder already exists.
        This assumption makes it slightly faster than the other functions that use create_file().
        Necessary since this one is often used in real time (before simulations, etc..) and not in
        one-off scenarios like the others (when making a release).
        """
        with open(join(output_path, self.register_list.name + "_regs_pkg.vhd"), "w") as file_handle:
            file_handle.write(RegisterVhdlGenerator(self.register_list).get_package())

    def create_c_header(self, output_path):
        output_file = join(output_path, self.register_list.name + "_regs.h")
        create_file(output_file, RegisterCGenerator(self.register_list).get_header())

    def create_cpp_interface(self, output_path):
        output_file = join(output_path, "i_" + self.register_list.name + ".h")
        create_file(output_file, RegisterCppGenerator(self.register_list).get_interface())

    def create_cpp_header(self, output_path):
        output_file = join(output_path, self.register_list.name + ".h")
        create_file(output_file, RegisterCppGenerator(self.register_list).get_header())

    def create_cpp_implementation(self, output_path):
        output_file = join(output_path, self.register_list.name + ".cpp")
        create_file(output_file, RegisterCppGenerator(self.register_list).get_implementation())

    def create_html_page(self, output_path):
        output_file = join(output_path, self.register_list.name + "_regs.html")
        create_file(output_file, RegisterHtmlGenerator(self.register_list).get_page())

    def create_html_table(self, output_path):
        output_file = join(output_path, self.register_list.name + "_regs_table.html")
        create_file(output_file, RegisterHtmlGenerator(self.register_list).get_table())


def load_json_file(file_name):
    def check_for_duplicate_keys(ordered_pairs):
        """
        Raise ValueError if a duplicate key exists
        Note that built in dictionaries are not ordered, hence OrderedDict
        """
        result = OrderedDict()
        for key, value in ordered_pairs:
            if key in result:
                raise ValueError(f"Duplicate key {key}")
            result[key] = value
        return result

    try:
        with open(file_name) as file_handle:
            return json.load(file_handle, object_pairs_hook=check_for_duplicate_keys)
    except ValueError as exception_info:
        message = f"Error while parsing JSON file {file_name}:\n{exception_info}"
        raise ValueError(message)
    except FileNotFoundError:
        raise FileNotFoundError(f"Requested json file does not exist: {file_name}")


def from_json(module_name, json_file, default_registers=None):
    json_data = load_json_file(json_file)
    register_list = RegisterList(module_name)
    if default_registers is not None:
        register_list.registers = default_registers

    for register_name, register_fields in json_data.items():
        if default_registers is not None and register_name in default_registers:
            # Default registers can be "updated" in the sense that the user can use a custom
            # description and add whatever bits they use in the current module. They can not however
            # change the mode.
            register = register_list.registers[register_name]
            if "mode" in register_fields:
                mesg = f"Overloading register {register_name} in {json_file}, one can not change mode from default"
                raise ValueError(mesg)
        else:
            # If it is a new register however the mode has to be specified.
            if "mode" not in register_fields:
                raise ValueError(f"Register {register_name} in {json_file} does not have mode field")
            register = register_list.append(register_name, register_fields["mode"])

        if "description" in register_fields:
            register.description = register_fields["description"]

        if "bits" in register_fields:
            for bit_name, bit_description in register_fields["bits"].items():
                register.append_bit(bit_name, bit_description)

    return Registers(register_list)
