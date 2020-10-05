# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

import hashlib
import datetime
import re
from shutil import copy2

import toml

from tsfpga.git_utils import git_commands_are_available, get_git_commit
from tsfpga.svn_utils import svn_commands_are_available, get_svn_revision_information
from tsfpga.system_utils import create_directory, create_file, read_file
from .register_types import Constant, Register, RegisterArray
from .register_c_generator import RegisterCGenerator
from .register_cpp_generator import RegisterCppGenerator
from .register_html_generator import RegisterHtmlGenerator
from .register_vhdl_generator import RegisterVhdlGenerator


class RegisterList:

    """
    Used to handle the registers of a module. Also known as a register map.
    """

    def __init__(self, name, source_definition_file, source_definition_hash):
        """
        Arguments:
            name (str): The name of this register list. Typically the name of the module that uses
                it.
            source_definition_file (`pathlib.Path`): The TOML source file that defined this
                register list.
            source_definition_hash (str): Has of the source definition file. Is used to detect
                if a re-generate of output files is needed.
        """
        self.name = name
        self.source_definition_file = source_definition_file
        self._source_definition_hash = source_definition_hash

        self.register_objects = []
        self.constants = []

    def append_register(self, name, mode, description=None, default_value=None):
        """
        Append a register to this list.

        Arguments:
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

        Arguments:
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

        Arguments:
            name (str): The name of the register.
        Return:
            :class:`.Register`: The register. ``None`` if no register matched.
        """
        for register_object in self.register_objects:
            if register_object.name == name:
                return register_object

        return None

    def add_constant(self, name, value, description=None):
        """
        Add a constant. Will be available in the generated packages and headers.

        Arguments:
            name (str): The name of the constant.
            length (int): The constant value (signed).
            description (str): Textual description for the constant.
        Return:
            :class:`.Constant`: The constant object that was created.
        """
        constant = Constant(name, value, description)
        self.constants.append(constant)
        return constant

    def get_constant(self, name):
        """
        Get a constant from this list.

        Arguments:
            name (str): The name of the constant.
        Return:
            :class:`.Constant`: The constant. ``None`` if no constant matched.
        """
        for constant in self.constants:
            if constant.name == name:
                return constant

        return None

    def create_vhdl_package(self, output_path):
        """
        Create a VHDL package file with register and field definitions.

        This function assumes that the ``output_path`` folder already exists. This assumption makes
        it slightly faster than the other functions that use create_file()``. Necessary since this
        one is often used in real time (before simulations, etc..) and not in one-off scenarios
        like the others (when making a release).

        In order to save time, there is a mechanism to only generated the VHDL file when necessary.
        If there is a file existing, that was created based on an identical TOML source, then
        the file will not be re-generated.

        Arguments:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        vhd_file = output_path / (self.name + "_regs_pkg.vhd")
        if self._should_create_vhdl_package(vhd_file):
            self._create_vhdl_package(vhd_file)

    def _should_create_vhdl_package(self, vhd_file):
        if not vhd_file.exists():
            return True
        if self._source_definition_hash != self._find_hash_of_existing_vhdl_package(vhd_file):
            return True
        return False

    @staticmethod
    def _find_hash_of_existing_vhdl_package(vhd_file):
        """
        Returns `None` if nothing found, otherwise the matching string.
        """
        regexp = re.compile(
            r"\A-- This file is automatically generated by tsfpga\. "
            r"Source file hash ([0-9a-f]+)\.\n"
        )
        existing_file_content = read_file(vhd_file)
        match = regexp.search(existing_file_content)
        if match is None:
            return None
        return match.group(1)

    def _create_vhdl_package(self, vhd_file):
        print(f"Creating VHDL register package {vhd_file}.")
        generated_info = f"{self.generated_info()} Source file hash {self._source_definition_hash}."
        register_vhdl_generator = RegisterVhdlGenerator(self.name, generated_info)
        with vhd_file.open("w") as file_handle:
            file_handle.write(
                register_vhdl_generator.get_package(self.register_objects, self.constants)
            )

    def create_c_header(self, output_path):
        """
        Create a C header file with register and field definitions.

        Arguments:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + "_regs.h")
        register_c_generator = RegisterCGenerator(self.name, self.generated_source_info())
        create_file(
            output_file, register_c_generator.get_header(self.register_objects, self.constants)
        )

    def create_cpp_interface(self, output_path):
        """
        Create a C++ class interface header file, with register and field definitions. The
        interface header contains only virtual methods.

        Arguments:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / ("i_" + self.name + ".h")
        register_cpp_generator = RegisterCppGenerator(self.name, self.generated_source_info())
        create_file(
            output_file, register_cpp_generator.get_interface(self.register_objects, self.constants)
        )

    def create_cpp_header(self, output_path):
        """
        Create a C++ class header file.

        Arguments:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + ".h")
        register_cpp_generator = RegisterCppGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_cpp_generator.get_header(self.register_objects))

    def create_cpp_implementation(self, output_path):
        """
        Create a C++ class implementation file.

        Arguments:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + ".cpp")
        register_cpp_generator = RegisterCppGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_cpp_generator.get_implementation(self.register_objects))

    def create_html_page(self, output_path):
        """
        Create a documentation HTML page with register and field information. Will include the
        tables created by :meth:`.create_html_register_table` and
        :meth:`.create_html_constant_table`.

        Arguments:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + "_regs.html")
        register_html_generator = RegisterHtmlGenerator(self.name, self.generated_source_info())
        create_file(
            output_file, register_html_generator.get_page(self.register_objects, self.constants)
        )

    def create_html_register_table(self, output_path):
        """
        Create documentation HTML table with register and field information.

        Arguments:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + "_register_table.html")
        register_html_generator = RegisterHtmlGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_html_generator.get_register_table(self.register_objects))

    def create_html_constant_table(self, output_path):
        """
        Create documentation HTML table with constant information.

        Arguments:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + "_constant_table.html")
        register_html_generator = RegisterHtmlGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_html_generator.get_constant_table(self.constants))

    def copy_source_definition(self, output_path):
        """
        Copy the TOML file that created this register list.

        Arguments:
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
        return "This file is automatically generated by tsfpga."

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


def load_toml_file(toml_file):
    if not toml_file.exists():
        raise FileNotFoundError(f"Requested TOML file does not exist: {toml_file}")

    raw_toml = read_file(toml_file)
    try:
        return toml.loads(raw_toml), _get_hash(raw_toml)
    except toml.TomlDecodeError as exception_info:
        message = f"Error while parsing TOML file {toml_file}:\n{exception_info}"
        raise ValueError(message) from exception_info


def _get_hash(data):
    """
    Get a hash of the data. SHA1 is the fastest method according to e.g.
    http://atodorov.org/blog/2013/02/05/performance-test-md5-sha1-sha256-sha512/
    Result is a lowercase hexadecimal string.
    """
    return hashlib.sha1(data.encode()).hexdigest()


RECOGNIZED_CONSTANT_ITEMS = {"value", "description"}
RECOGNIZED_REGISTER_ITEMS = {"mode", "default_value", "description", "bits"}
RECOGNIZED_REGISTER_ARRAY_ITEMS = {"array_length", "register"}


def from_toml(module_name, toml_file, default_registers=None):
    toml_data, toml_data_hash = load_toml_file(toml_file)
    register_list = RegisterList(
        name=module_name, source_definition_file=toml_file, source_definition_hash=toml_data_hash
    )

    default_register_names = []
    if default_registers is not None:
        register_list.register_objects = default_registers
        for register in default_registers:
            default_register_names.append(register.name)

    names_taken = set()

    if "register" in toml_data:
        for name, items in toml_data["register"].items():
            _parse_plain_register(
                name, items, register_list, default_register_names, names_taken, toml_file
            )

    if "register_array" in toml_data:
        for name, items in toml_data["register_array"].items():
            _parse_register_array(name, items, register_list, names_taken, toml_file)

    if "constant" in toml_data:
        for name, items in toml_data["constant"].items():
            _parse_constant(name, items, register_list, toml_file)

    return register_list


def _parse_constant(name, items, register_list, toml_file):
    constant = Constant(name=name, value=items["value"])

    for item_name, item_value in items.items():
        if item_name not in RECOGNIZED_CONSTANT_ITEMS:
            message = (
                f"Error while parsing constant {name} in {toml_file}:\nUnknown key {item_name}"
            )
            raise ValueError(message)

        if item_name == "description":
            constant.description = item_value

    register_list.constants.append(constant)


def _parse_plain_register(
    name, items, register_list, default_register_names, names_taken, toml_file
):
    if "array_length" in items:
        message = f"Plain register {name} in {toml_file} can not have array_length attribute"
        raise ValueError(message)

    if name in default_register_names:
        # Default registers can be "updated" in the sense that the user can use a custom
        # description and add whatever bits they use in the current module. They can not however
        # change the mode.
        register = register_list.get_register(name)
        if "mode" in items:
            message = (
                f"Overloading register {name} in {toml_file}, one can not change mode from default"
            )
            raise ValueError(message)
    else:
        # If it is a new register however the mode has to be specified.
        if "mode" not in items:
            raise ValueError(f"Register {name} in {toml_file} does not have mode field")
        register = register_list.append_register(name, items["mode"])

    for item_name, item_value in items.items():
        if item_name not in RECOGNIZED_REGISTER_ITEMS:
            message = (
                f"Error while parsing register {name} in {toml_file}:\nUnknown key {item_name}"
            )
            raise ValueError(message)
        if item_name == "default_value":
            register.default_value = item_value

        if item_name == "description":
            register.description = item_value

        if item_name == "bits":
            for bit_name, bit_description in item_value.items():
                register.append_bit(bit_name, bit_description)

    names_taken.add(name)


# pylint: disable=too-many-locals
def _parse_register_array(name, items, register_list, names_taken, toml_file):
    if name in names_taken:
        message = f"Duplicate name {name} in {toml_file}"
        raise ValueError(message)
    if "array_length" not in items:
        message = f"Register array {name} in {toml_file} does not have array_length attribute"
        raise ValueError(message)

    for item_name in items:
        if item_name not in RECOGNIZED_REGISTER_ARRAY_ITEMS:
            message = (
                f"Error while parsing register array {name} in {toml_file}:\n"
                f"Unknown key {item_name}"
            )
            raise ValueError(message)

    length = items["array_length"]
    register_array = register_list.append_register_array(name, length)

    for register_name, register_items in items["register"].items():
        if "mode" not in register_items:
            message = (
                f"Register {register_name} within array {name} in {toml_file} "
                "does not have mode field"
            )
            raise ValueError(message)
        register = register_array.append_register(register_name, register_items["mode"])

        for register_item_name, register_item_value in register_items.items():
            if register_item_name not in RECOGNIZED_REGISTER_ITEMS:
                message = (
                    f"Error while parsing register {register_name} in array {name} in "
                    f"{toml_file}:\nUnknown key {register_item_name}"
                )
                raise ValueError(message)
            if register_item_name == "default_value":
                register.default_value = register_item_value

            if register_item_name == "description":
                register.description = register_item_value

            if register_item_name == "bits":
                for bit_name, bit_description in register_item_value.items():
                    register.append_bit(bit_name, bit_description)
