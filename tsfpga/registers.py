# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from collections import OrderedDict
import datetime
import json
from shutil import copy2

from tsfpga.git_utils import git_commands_are_available, get_git_commit
from tsfpga.register_c_generator import RegisterCGenerator
from tsfpga.register_cpp_generator import RegisterCppGenerator
from tsfpga.register_html_generator import RegisterHtmlGenerator
from tsfpga.register_vhdl_generator import RegisterVhdlGenerator
from tsfpga.svn_utils import svn_commands_are_available, get_svn_revision_information
from tsfpga.system_utils import create_directory, create_file


class Bit:

    """
    Used to represent a bit in a register.
    """

    def __init__(self, name, index, description):
        """
        Args:
            name (str): The name of the bit.
            index (int): The zero-based index of this bit within the register.
            description (str): Textual bit description.
        """
        self.name = name
        self.index = index
        self.description = description


class Register:

    """
    Used to represent a register and its fields.
    """

    def __init__(self, name, index, mode, description=""):
        """
        Args:
            name (str): The name of the register.
            index (int): The zero-based index of this register in its register list.
            mode (str): A valid register mode.
            description (str): Textual register description.
        """
        self.name = name
        self.index = index
        self.mode = mode
        self.description = description
        self.bits = []

    def append_bit(self, name, description):
        """
        Append a bit to this register.

        Args:
            name (str): The name of the bit.
            description (str): Description of the bit.
        Return:
            :class:`.Bit`: The bit object that was created.
        """
        index = len(self.bits)
        bit = Bit(name, index, description)

        self.bits.append(bit)
        return bit

    @property
    def address(self):
        """
        int: Byte address, within the register list, of this register.
        """
        return 4 * self.index

    @property
    def is_bus_readable(self):
        """
        True if the register is readable by bus. Based on the register type.
        """
        return self.mode in ["r", "r_w", "r_wpulse"]

    @property
    def is_bus_writeable(self):
        """
        True if the register is writeable by bus. Based on the register type.
        """
        return self.mode in ["w", "r_w", "wpulse", "r_wpulse"]


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
        self.registers = []

    def append_register(self, name, mode):
        """
        Append a register to this list.

        Args:
            name (str): The name of the register.
            mode (str): A valid register mode.
        Return:
            :class:`.Register`: The register object that was created.
        """
        index = len(self.registers)
        register = Register(name, index, mode)

        self.registers.append(register)
        return register

    def get_register(self, name):
        """
        Get a register from this list.

        Args:
            name (str): The name of the register.
        Return:
            :class:`.Register`: The register. ``None`` if no register matched.
        """
        for register in self.registers:
            if register.name == name:
                return register

        return None

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
            file_handle.write(register_vhdl_generator.get_package(self.registers))

    def create_c_header(self, output_path):
        """
        Create a C header file with register and field definitions.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + "_regs.h")
        register_c_generator = RegisterCGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_c_generator.get_header(self.registers))

    def create_cpp_interface(self, output_path):
        """
        Create a C++ class interface header file, with register and field definitions. The interface header
        contains only virtual methods.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / ("i_" + self.name + ".h")
        register_cpp_generator = RegisterCppGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_cpp_generator.get_interface(self.registers))

    def create_cpp_header(self, output_path):
        """
        Create a C++ class header file.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + ".h")
        register_cpp_generator = RegisterCppGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_cpp_generator.get_header(self.registers))

    def create_cpp_implementation(self, output_path):
        """
        Create a C++ class implementation file.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + ".cpp")
        register_cpp_generator = RegisterCppGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_cpp_generator.get_implementation(self.registers))

    def create_html_page(self, output_path):
        """
        Create a documentation HTML page with register and field information. Will include the
        table created by :meth:`.create_html_table`.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + "_regs.html")
        register_html_generator = RegisterHtmlGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_html_generator.get_page(self.registers))

    def create_html_table(self, output_path):
        """
        Create documentation HTML table with register and field information.

        Args:
            output_path (`pathlib.Path`): Result will be placed here.
        """
        output_file = output_path / (self.name + "_regs_table.html")
        register_html_generator = RegisterHtmlGenerator(self.name, self.generated_source_info())
        create_file(output_file, register_html_generator.get_table(self.registers))

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
        register_list.registers = default_registers
        for register in default_registers:
            default_register_names.append(register.name)

    for register_name, register_fields in json_data.items():
        if register_name in default_register_names:
            # Default registers can be "updated" in the sense that the user can use a custom
            # description and add whatever bits they use in the current module. They can not however
            # change the mode.
            register = register_list.get_register(register_name)
            if "mode" in register_fields:
                message = f"Overloading register {register_name} in {json_file}, one can not change mode from default"
                raise ValueError(message)
        else:
            # If it is a new register however the mode has to be specified.
            if "mode" not in register_fields:
                raise ValueError(f"Register {register_name} in {json_file} does not have mode field")
            register = register_list.append_register(register_name, register_fields["mode"])

        if "description" in register_fields:
            register.description = register_fields["description"]

        if "bits" in register_fields:
            for bit_name, bit_description in register_fields["bits"].items():
                register.append_bit(bit_name, bit_description)

    return register_list
