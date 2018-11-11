from os.path import join, exists
from collections import OrderedDict
import json

from hdl_reuse.register_html_generator import RegisterHtmlGenerator
from hdl_reuse.register_vhdl_generator import RegisterVhdlGenerator
from hdl_reuse.register_list import RegisterList
from hdl_reuse.system_utils import create_file
from hdl_reuse.register_c_generator import RegisterCGenerator


class Registers:

    def __init__(self, register_list):
        self.register_list = register_list

    def create_vhdl_package(self, output_file):
        """
        Assumes that the containing folder already exists.
        This assumption makes it slightly faster that the other functions that use create_file().
        Necessary since this one is often used in real time (before simulations, etc..) and not in
        one off scenarios like the others (when making a release).
        """
        with open(output_file, "w") as file_handle:
            file_handle.write(RegisterVhdlGenerator(self.register_list).get_package())

    def create_c_header(self, output_path):
        output_file = join(output_path, self.register_list.name + "_regs.h")
        create_file(output_file, RegisterCGenerator(self.register_list).get_header())

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
            else:
                result[key] = value
        return result

    if not exists(file_name):
        raise ValueError(f"Requested json file does not exist: {file_name}")

    with open(file_name) as file_handle:
        try:
            return json.load(file_handle, object_pairs_hook=check_for_duplicate_keys)
        except ValueError as exception_info:
            message = f"Error while parsing JSON file {file_name}:\n%s" % exception_info
            raise ValueError(message)


def from_json(module_name, json_file):
    register_list = RegisterList(module_name)
    json_data = load_json_file(json_file)

    for register_name, register_fields in json_data.items():
        if "mode" not in register_fields:
            raise ValueError(f"Register {register_name} in {json_file} does not have mode field")

        register = register_list.append(register_name, register_fields["mode"])
        if "description" in register_fields:
            register.description = register_fields["description"]

        if "bits" in register_fields:
            for bit_name, bit_description in register_fields["bits"].items():
                register.append_bit(bit_name, bit_description)

    return Registers(register_list)
