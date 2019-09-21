# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class RegisterCppGenerator:

    def __init__(self, register_list):
        self.register_list = register_list
        self._class_name = self._to_pascal_case(register_list.name)

    def get_interface(self):
        cpp_code = f"class I{self._class_name}\n"
        cpp_code += "{\n"
        cpp_code += "public:\n"

        for register in self.register_list.registers.values():
            bits = register.bits
            if bits:
                for bit in bits:
                    bit_constant_name = register.name + "_" + bit.name
                    bit_constant_value = 2 ** bit.idx
                    cpp_code += f"  static const uint32_t {bit_constant_name} = {bit_constant_value}uL;\n"
                cpp_code += "\n"

        cpp_code += f"  virtual ~I{self._class_name}() {{ }}\n\n"
        for register in self.register_list.registers.values():
            if register.is_ps_readable:
                cpp_code += f"  virtual {self._getter_function_signature(register)} const = 0;\n"
            if register.is_ps_writeable:
                cpp_code += f"  virtual {self._setter_function_signature(register)} const = 0;\n"
            cpp_code += "\n"
        cpp_code += "};\n"

        cpp_code_top = f"""
{self._file_header()}
#pragma once

#include <cstdint>

"""
        return cpp_code_top + self._with_namespace(cpp_code)

    def get_header(self):
        cpp_code = f"class {self._class_name} : public I{self._class_name}\n"
        cpp_code += "{\n"

        cpp_code += "private:\n"
        cpp_code += "  volatile uint32_t *m_registers;\n\n"

        cpp_code += "public:\n"
        cpp_code += f"  {self._constructor_signature()};\n\n"
        cpp_code += f"  virtual ~{self._class_name}() {{ }}\n\n"
        for register in self.register_list.registers.values():
            if register.is_ps_readable:
                cpp_code += f"  virtual {self._getter_function_signature(register)} const override;\n"
            if register.is_ps_writeable:
                cpp_code += f"  virtual {self._setter_function_signature(register)} const override;\n"
            cpp_code += "\n"
        cpp_code += "};\n"

        cpp_code_top = f"""
{self._file_header()}
#pragma once

#include "i_{self.register_list.name}.h"

"""
        return cpp_code_top + self._with_namespace(cpp_code)

    def get_implementation(self):
        cpp_code = f"{self._class_name}::{self._constructor_signature()}\n"
        cpp_code += "    : m_registers(reinterpret_cast<volatile uint32_t *>(base_address))\n"
        cpp_code += "{\n"
        cpp_code += "  // Empty\n"
        cpp_code += "}\n\n"

        for register in self.register_list.registers.values():
            if register.is_ps_readable:
                cpp_code += self._getter_function(register)
            if register.is_ps_writeable:
                cpp_code += self._setter_function(register)

        cpp_code_top = f"{self._file_header()}\n"
        cpp_code_top += f"#include \"include/{self.register_list.name}.h\"\n\n"

        return cpp_code_top + self._with_namespace(cpp_code)

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
        cpp_code = self._comment(self.register_list.generated_info())
        cpp_code += self._comment(self.register_list.generated_source_info())
        return cpp_code

    @staticmethod
    def _to_pascal_case(snake_string):
        """
        Returns e.g., my_funny_string -> MyFunnyString
        """
        return snake_string.title().replace("_", "")

    def _constructor_signature(self):
        return f"{self._class_name}(volatile uint8_t *base_address)"

    def _setter_function(self, register):
        cpp_code = f"void {self._class_name}::set_{register.name}(uint32_t value) const\n"
        cpp_code += "{\n"
        cpp_code += f"  m_registers[{register.idx}] = value;\n"
        cpp_code += "}\n\n"
        return cpp_code

    @staticmethod
    def _setter_function_signature(register):
        return f"void set_{register.name}(uint32_t value)"

    def _getter_function(self, register):
        cpp_code = f"uint32_t {self._class_name}::get_{register.name}() const\n"
        cpp_code += "{\n"
        cpp_code += f"  return m_registers[{register.idx}];\n"
        cpp_code += "}\n\n"
        return cpp_code

    @staticmethod
    def _getter_function_signature(register):
        return f"uint32_t get_{register.name}()"
