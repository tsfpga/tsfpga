# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


from tsfpga.register_code_generator import RegisterCodeGenerator
from tsfpga.register_types import Register, RegisterArray


class RegisterVhdlGenerator(RegisterCodeGenerator):

    def __init__(self, module_name, generated_info):
        self.module_name = module_name
        self.generated_info = generated_info

    @staticmethod
    def _comment(comment):
        return f"-- {comment}\n"

    def _header(self):
        return self._comment(self.generated_info)

    def _register_name(self, register, register_array=None):
        if register_array is None:
            return f"{self.module_name}_{register.name}"
        return f"{self.module_name}_{register_array.name}_{register.name}"

    def _register_function_signature(self, register, register_array):
        return f"function {self._register_name(register, register_array)}(array_index : natural) return integer"

    def _register_indexes(self, register_objects):
        vhdl = ""
        for register, register_array in self._iterate_registers(register_objects):
            if register_array is None:
                vhdl += f"  constant {self._register_name(register)} : integer := {register.index};\n"
            else:
                vhdl += f"  {self._register_function_signature(register, register_array)};\n"

        return vhdl

    def _array_length_constant_name(self, register_array):
        return f"{self.module_name}_{register_array.name}_array_length"

    def _array_constants(self, register_objects):
        vhdl = ""
        for register_object in register_objects:
            if isinstance(register_object, RegisterArray):
                constant = self._array_length_constant_name(register_object)
                vhdl += f"  constant {constant} : integer := {register_object.length};\n"
        if vhdl:
            vhdl += "\n"

        return vhdl

    def _register_map(self, register_objects):
        map_name = f"{self.module_name}_reg_map"

        register_definitions = []
        default_values = []
        for register_object in register_objects:
            if isinstance(register_object, Register):
                idx = self._register_name(register_object)
                register_definitions.append(f"  (idx => {idx}, reg_type => {register_object.mode})")
                default_values.append(f"  std_logic_vector(to_signed({register_object.default_value}, 32))")
            else:
                for array_index in range(register_object.length):
                    for register in register_object.registers:
                        idx = f"{self._register_name(register, register_object)}({array_index})"
                        register_definitions.append(f"  (idx => {idx}, reg_type => {register.mode})")
                        default_values.append(f"  std_logic_vector(to_signed({register.default_value}, 32))")

        last_index = register_objects[-1].index
        vhdl = f"  constant {map_name} : reg_definition_vec_t(0 to {last_index}) := (\n  "
        vhdl += ",\n  ".join(register_definitions)
        vhdl += "\n  );\n"
        vhdl += "\n"
        vhdl += f"  subtype {self.module_name}_regs_t is reg_vec_t({map_name}'range);\n"
        vhdl += f"  subtype {self.module_name}_reg_was_written_t is std_logic_vector({map_name}'range);\n"
        vhdl += f"  constant {self.module_name}_regs_init : {self.module_name}_regs_t := (\n  "
        vhdl += ",\n  ".join(default_values)
        vhdl += "\n  );\n"
        return vhdl

    def _register_bits(self, register_objects):
        vhdl = ""
        for register, register_array in self._iterate_registers(register_objects):
            for bit in register.bits:
                name = f"{self._register_name(register, register_array)}_{bit.name}"
                vhdl += f"  constant {name} : integer := {bit.index};\n"
            if register.bits:
                vhdl += "\n"

        return vhdl

    def _array_index_functions(self, register_objects):
        vhdl = ""
        for register_object in register_objects:
            if isinstance(register_object, RegisterArray):
                num_registers = len(register_object.registers)
                array_length = self._array_length_constant_name(register_object)
                for register in register_object.registers:
                    vhdl += f"  {self._register_function_signature(register, register_object)} is\n"
                    vhdl += "  begin\n"
                    vhdl += f"    assert array_index < {array_length} \n"
                    vhdl += "      report \"Array index out of bounds: \" & to_string(array_index)\n"
                    vhdl += "      severity failure;\n"
                    vhdl += f"    return {register_object.base_index} + array_index * {num_registers} + {register.index};\n"
                    vhdl += "  end function;\n\n"

        return vhdl

    def _constants(self, constants):
        vhdl = ""
        for constant in constants:
            vhdl += f"  constant {self.module_name}_constant_{constant.name} : integer := {constant.value};\n"
        return vhdl

    def get_package(self, register_objects, constants):
        pkg_name = f"{self.module_name}_regs_pkg"

        vhdl = f"""\
{self._header()}
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library reg_file;
use reg_file.reg_file_pkg.all;


package {pkg_name} is

{self._register_indexes(register_objects)}
{self._array_constants(register_objects)}\
{self._register_map(register_objects)}
{self._register_bits(register_objects)}\
{self._constants(constants)}
end package;

package body {pkg_name} is

{self._array_index_functions(register_objects)}\
end package body;
"""

        return vhdl
