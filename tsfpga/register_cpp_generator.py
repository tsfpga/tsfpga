# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.register_code_generator import RegisterCodeGenerator
from tsfpga.register_types import Register


class RegisterCppGenerator(RegisterCodeGenerator):

    def __init__(self, module_name, generated_info):
        self.module_name = module_name
        self.generated_info = generated_info
        self._class_name = self._to_pascal_case(module_name)

    def get_interface(self, register_objects, constants):
        cpp_code = f"class I{self._class_name}\n"
        cpp_code += "{\n"
        cpp_code += "public:\n"

        for constant in constants:
            cpp_code += f"  static const int {constant.name} = {constant.value}L;\n"
        cpp_code += f"  static const size_t num_registers = {register_objects[-1].index + 1}uL;\n\n"

        for register_object in register_objects:
            if isinstance(register_object, Register):
                cpp_code += self._bit_constants(register_object)
            else:
                constant_name = self._array_length_constant_name(register_object)
                cpp_code += f"  static const size_t {constant_name} = {register_object.length}uL;\n\n"

                for register in register_object.registers:
                    cpp_code += self._bit_constants(register, register_object.name)

        cpp_code += f"  virtual ~I{self._class_name}() {{ }}\n"

        for register, register_array in self._iterate_registers(register_objects):
            cpp_code += "\n"
            if register.is_bus_readable:
                cpp_code += f"  virtual uint32_t {self._getter_function_signature(register, register_array)} const = 0;\n"
            if register.is_bus_writeable:
                cpp_code += f"  virtual void {self._setter_function_signature(register, register_array)} const = 0;\n"

        cpp_code += "};\n"

        cpp_code_top = f"""\
{self._file_header()}
#pragma once

#include <cassert>
#include <cstdint>
#include <cstdlib>

"""
        return cpp_code_top + self._with_namespace(cpp_code)

    def get_header(self, register_objects):
        cpp_code = f"class {self._class_name} : public I{self._class_name}\n"
        cpp_code += "{\n"

        cpp_code += "private:\n"
        cpp_code += "  volatile uint32_t *m_registers;\n\n"

        cpp_code += "public:\n"
        cpp_code += f"  {self._constructor_signature()};\n\n"
        cpp_code += f"  virtual ~{self._class_name}() {{ }}\n"

        for register, register_array in self._iterate_registers(register_objects):
            cpp_code += "\n"
            if register.is_bus_readable:
                cpp_code += f"  virtual uint32_t {self._getter_function_signature(register, register_array)} const override;\n"
            if register.is_bus_writeable:
                cpp_code += f"  virtual void {self._setter_function_signature(register, register_array)} const override;\n"

        cpp_code += "};\n"

        cpp_code_top = f"""\
{self._file_header()}
#pragma once

#include "i_{self.module_name}.h"

"""
        return cpp_code_top + self._with_namespace(cpp_code)

    def get_implementation(self, register_objects):
        cpp_code = f"{self._class_name}::{self._constructor_signature()}\n"
        cpp_code += "    : m_registers(reinterpret_cast<volatile uint32_t *>(base_address))\n"
        cpp_code += "{\n"
        cpp_code += "  // Empty\n"
        cpp_code += "}\n\n"

        for register, register_array in self._iterate_registers(register_objects):
            if register.is_bus_readable:
                cpp_code += self._getter_function(register, register_array)
            if register.is_bus_writeable:
                cpp_code += self._setter_function(register, register_array)

        cpp_code_top = f"{self._file_header()}\n"
        cpp_code_top += f"#include \"include/{self.module_name}.h\"\n\n"

        return cpp_code_top + self._with_namespace(cpp_code)

    @staticmethod
    def _bit_constants(register, name_prefix=None):
        cpp_code = ""
        for bit in register.bits:
            if name_prefix is None:
                bit_constant_name = f"{register.name}_{bit.name}"
            else:
                bit_constant_name = f"{name_prefix}_{register.name}_{bit.name}"

            bit_constant_value = 2 ** bit.index
            cpp_code += f"  static const uint32_t {bit_constant_name} = {bit_constant_value}uL;\n"

        if cpp_code:
            cpp_code += "\n"

        return cpp_code

    @staticmethod
    def _array_length_constant_name(register_array):
        return f"{register_array.name}_array_length"

    @staticmethod
    def _with_namespace(cpp_code_body):
        cpp_code = "namespace fpga_regs\n"
        cpp_code += "{\n\n"
        cpp_code += f"{cpp_code_body}"
        cpp_code += "\n} /* namespace fpga_regs */\n"
        return cpp_code

    @staticmethod
    def _comment(comment):
        return f"/* {comment} */\n"

    def _file_header(self):
        return self._comment(self.generated_info)

    @staticmethod
    def _to_pascal_case(snake_string):
        """
        Returns e.g., my_funny_string -> MyFunnyString
        """
        return snake_string.title().replace("_", "")

    def _constructor_signature(self):
        return f"{self._class_name}(volatile uint8_t *base_address)"

    def _setter_function(self, register, register_array):
        cpp_code = f"void {self._class_name}::{self._setter_function_signature(register, register_array)} const\n"
        cpp_code += "{\n"
        if register_array is None:
            cpp_code += f"  m_registers[{register.index}] = value;\n"
        else:
            cpp_code += f"  assert(array_index < {self._array_length_constant_name(register_array)});\n"
            cpp_code += f"  const size_t index = "\
                f"{register_array.base_index} + array_index * {len(register_array.registers)} + {register.index};\n"
            cpp_code += "  m_registers[index] = value;\n"
        cpp_code += "}\n\n"
        return cpp_code

    @staticmethod
    def _setter_function_signature(register, register_array):
        if register_array is None:
            return f"set_{register.name}(uint32_t value)"
        return f"set_{register_array.name}_{register.name}(size_t array_index, uint32_t value)"

    def _getter_function(self, register, register_array):
        cpp_code = f"uint32_t {self._class_name}::{self._getter_function_signature(register, register_array)} const\n"
        cpp_code += "{\n"
        if register_array is None:
            cpp_code += f"  return m_registers[{register.index}];\n"
        else:
            cpp_code += f"  assert(array_index < {self._array_length_constant_name(register_array)});\n"
            cpp_code += f"  const size_t index = "\
                f"{register_array.base_index} + array_index * {len(register_array.registers)} + {register.index};\n"
            cpp_code += "  return m_registers[index];\n"
        cpp_code += "}\n\n"
        return cpp_code

    @staticmethod
    def _getter_function_signature(register, register_array):
        if register_array is None:
            return f"get_{register.name}()"
        return f"get_{register_array.name}_{register.name}(size_t array_index)"
