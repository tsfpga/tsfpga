# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from collections import OrderedDict
import datetime
import json
from shutil import copy2

from tsfpga.git_utils import git_commands_are_available, get_git_commit
from tsfpga.register_types import Constant, Register, RegisterArray
from tsfpga.register_c_generator import RegisterCGenerator
from tsfpga.register_cpp_generator import RegisterCppGenerator
from tsfpga.register_html_generator import RegisterHtmlGenerator
from tsfpga.register_vhdl_generator import RegisterVhdlGenerator
from tsfpga.svn_utils import svn_commands_are_available, get_svn_revision_information
from tsfpga.system_utils import create_directory, create_file


class RegisterList:

    """
    Used to handle the registers of a module. Also known as a register map.
    """

    def __init__(self, name, source_definition_file):
        """
        Args:
            name (str): The name of this register list. Typically the name of the module that uses it.
            source_definition_file (`pathlib.Path`): The JSON source file that defined this register list.
        """
        self.name = name
        self.source_definition_file = source_definition_file
        self.register_objects = []
        self.constants = []

    def append_register(self, name, mode, description=None, default_value=None):
        """
        Append a register to this list.

        Args:
            name (str): The name of the register.
            mode (str): A valid register mode.
            description (str): Textual register description.
            default_value (int): Default value for the register (signed).
        Return:
            :class:`.Register`: The register object that was created.
        """
        if self.register_objects:
            index = self.register_objects[-1].index + 1
        else:
            index = 0

        register = Register(name, index, mode, description, default_value)
        self.register_objects.append(register)

        return register

    def append_register_array(self, name, length):
        """
        Append a register array to this list.

        Args:
            name (str): The name of the register array.
            length (int): The number of times the register sequence shall be repeated.
        Return:
            :class:`.RegisterArray`: The register array object that was created.
        """
        if self.register_objects:
            base_index = self.register_objects[-1].index + 1
        else:
            base_index = 0
        register_array = RegisterArray(name, base_index, length)

        self.register_objects.append(register_array)
        return register_array

    def get_register(self, name):
        """
        Get a register from this list. Will only find single registers, not registers in a
        register array.

        Args:
            name (str): The name of the register.
        Return:
            :class:`.Register`: The register. ``None`` if no register matched.
        """
        for register_object in self.register_objects:
            if register_object.name == name:
                return register_object

        return None

    def add_constant(self, name, value):
        """
        Add a constant. Will be available in the generated packages and headers.

        Args:
            name (str): The name of the constant.
            length (int): The constant value (signed).
        """
        self.constants.append(Constant(name, value))

    def create_vhdl_package(self, output_path):
        """
        Create a VHDL package file with register and field definitions.

        This function assumes that the ``output_path`` folder already exists.
        This assumption makes it slightly faster than the other functions that use ``create_file()``.
        Necessary since this one is often used in real time (before simulations, etc..) and not in
        one-off scenarios like the others (when making a release).

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        register_vhdl_generator = RegisterVhdlGenerator(self.name, self.generated_info())
        with (output_path / (self.name + "_regs_pkg.vhd")).open("w") as file_handle:
            file_handle.write(register_vhdl_generator.get_package(self.register_objects, self.constants))

    def create_c_header(self, output_path):
        """
        Create a C header file with register and field definitions.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + "_regs.h")
        register_c_generator = RegisterCGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_c_generator.get_header(self.register_objects, self.constants))

    def create_cpp_interface(self, output_path):
        """
        Create a C++ class interface header file, with register and field definitions. The interface header
        contains only virtual methods.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / ("i_" + self.name + ".h")
        register_cpp_generator = RegisterCppGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_cpp_generator.get_interface(self.register_objects, self.constants))

    def create_cpp_header(self, output_path):
        """
        Create a C++ class header file.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + ".h")
        register_cpp_generator = RegisterCppGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_cpp_generator.get_header(self.register_objects))

    def create_cpp_implementation(self, output_path):
        """
        Create a C++ class implementation file.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + ".cpp")
        register_cpp_generator = RegisterCppGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_cpp_generator.get_implementation(self.register_objects))

    def create_html_page(self, output_path):
        """
        Create a documentation HTML page with register and field information. Will include the
        table created by :meth:`.create_html_table`.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + "_regs.html")
        register_html_generator = RegisterHtmlGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_html_generator.get_page(self.register_objects))

    def create_html_table(self, output_path):
        """
        Create documentation HTML table with register and field information.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + "_regs_table.html")
        register_html_generator = RegisterHtmlGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_html_generator.get_table(self.register_objects))

    def copy_source_definition(self, output_path):
        """
        Copy the JSON file that created this register list.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        create_directory(output_path, empty=False)
        copy2(self.source_definition_file, output_path)

    @staticmethod
    def generated_info():
        """
        Return:
            str: A string informing the user that a file is automatically generated.
        """
        return "File automatically generated by tsfpga."

    def generated_source_info(self):
        """
        Return:
            str: A string informing the user that a file is automatically generated, containing
            info about the source of the generated register information.
        """
        time_info = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        commit_info = ""
        if git_commands_are_available():
            commit_info = f" at commit {get_git_commit()}"
        elif svn_commands_are_available():
            commit_info = f" at revision {get_svn_revision_information()}"

        info = f"Generated {time_info} from file {self.source_definition_file.name}{commit_info}."

        return f"{self.generated_info()} {info}"


def get_default_registers():
    """
    tsfpga default registers
    """
    registers = [
        Register("config", 0, "r_w", "Configuration register."),
        Register(
            "command", 1, "wpulse",
            "When this register is written, all '1's in the written word will be asserted for one "
            "clock cycle in the FPGA logic."),
        Register("status", 2, "r", "Status register."),
        Register(
            "irq_status", 3, "r_wpulse",
            "Reading a '1' in this register means the corresponding interrupt has triggered. Writing "
            "to this register will clear the interrupts where there is a '1' in the written word."),
        Register(
            "irq_mask", 4, "r_w",
            "A '1' in this register means that the corresponding interrupt is enabled. ")
    ]
    return registers


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
        with file_name.open() as file_handle:
            return json.load(file_handle, object_pairs_hook=check_for_duplicate_keys)
    except ValueError as exception_info:
        message = f"Error while parsing JSON file {file_name}:\n{exception_info}"
        raise ValueError(message)
    except FileNotFoundError:
        raise FileNotFoundError(f"Requested json file does not exist: {file_name}")


def from_json(module_name, json_file, default_registers=None):
    json_data = load_json_file(json_file)
    register_list = RegisterList(module_name, json_file)

    default_register_names = []
    if default_registers is not None:
        register_list.register_objects = default_registers
        for register in default_registers:
            default_register_names.append(register.name)

    for name, items in json_data.items():
        if "registers" in items:
            _parse_register_array(name, items, register_list, json_file)
        else:
            _parse_plain_register(name, items, register_list, default_register_names, json_file)

    return register_list


RECOGNIZED_REGISTER_ITEMS = {"mode", "default_value", "description", "bits"}
RECOGNIZED_REGISTER_ARRAY_ITEMS = {"array_length", "registers"}


def _parse_plain_register(name, items, register_list, default_register_names, json_file):
    if "array_length" in items:
        message = f"Plain register {name} in {json_file} can not have array_length attribute"
        raise ValueError(message)

    if name in default_register_names:
        # Default registers can be "updated" in the sense that the user can use a custom
        # description and add whatever bits they use in the current module. They can not however
        # change the mode.
        register = register_list.get_register(name)
        if "mode" in items:
            message = f"Overloading register {name} in {json_file}, one can not change mode from default"
            raise ValueError(message)
    else:
        # If it is a new register however the mode has to be specified.
        if "mode" not in items:
            raise ValueError(f"Register {name} in {json_file} does not have mode field")
        register = register_list.append_register(name, items["mode"])

    for item_name, item_value in items.items():
        if item_name not in RECOGNIZED_REGISTER_ITEMS:
            message = f"Error while parsing register {name} in {json_file}:\nUnknown key {item_name}"
            raise ValueError(message)
        if item_name == "default_value":
            register.default_value = item_value

        if item_name == "description":
            register.description = item_value

        if item_name == "bits":
            for bit_name, bit_description in item_value.items():
                register.append_bit(bit_name, bit_description)


def _parse_register_array(name, items, register_list, json_file):
    if "array_length" not in items:
        message = f"Register array {name} in {json_file} does not have array_length attribute"
        raise ValueError(message)

    for item_name in items:
        if item_name not in RECOGNIZED_REGISTER_ARRAY_ITEMS:
            message = f"Error while parsing register array {name} in {json_file}:\n"\
                f"Unknown key {item_name}"
            raise ValueError(message)

    length = items["array_length"]
    register_array = register_list.append_register_array(name, length)

    for register_name, register_items in items["registers"].items():
        if "mode" not in register_items:
            message = f"Register {register_name} within array {name} in {json_file} does not have mode field"
            raise ValueError(message)
        register = register_array.append_register(register_name, register_items["mode"])

        for register_item_name, register_item_value in register_items.items():
            if register_item_name not in RECOGNIZED_REGISTER_ITEMS:
                message = f"Error while parsing register {register_name} in array {name} in " \
                    f"{json_file}:\nUnknown key {register_item_name}"
                raise ValueError(message)
            if register_item_name == "default_value":
                register.default_value = register_item_value

            if register_item_name == "description":
                register.description = register_item_value

            if register_item_name == "bits":
                for bit_name, bit_description in register_item_value.items():
                    register.append_bit(bit_name, bit_description)
