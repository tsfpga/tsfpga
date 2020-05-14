# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.register_code_generator import RegisterCodeGenerator
from tsfpga.register_types import Register


class RegisterCGenerator(RegisterCodeGenerator):

    def __init__(self, module_name, generated_info):
        self.module_name = module_name
        self.generated_info = generated_info

    def get_header(self, register_objects, constants):
        define_name = self.module_name.upper() + "_REGS_H"

        c_code = f"""\
{self._file_header()}
#ifndef {define_name}
#define {define_name}
#pragma pack(push, 1)

#include <stdint.h>

{self._register_struct(register_objects)}
{self._register_defines(register_objects)}\
{self._constants(constants)}
#pragma pack(pop)
#endif {self._comment(define_name)}"""

        return c_code

    @staticmethod
    def _comment(comment):
        return f"/* {comment} */\n"

    def _file_header(self):
        return self._comment(self.generated_info)

    def _register_struct(self, register_objects):
        array_structs = ""

        register_struct_type = f"{self.module_name}_regs_t"
        register_struct = f"typedef struct {register_struct_type}\n"
        register_struct += "{\n"
        for register_object in register_objects:
            if isinstance(register_object, Register):
                register_struct += f"  uint32_t {register_object.name};\n"
            else:
                array_struct_type = f"{self.module_name}_{register_object.name}_t"

                array_structs = f"typedef struct {array_struct_type}\n"
                array_structs += "{\n"
                for register in register_object.registers:
                    array_structs += f"  uint32_t {register.name};\n"
                array_structs += f"}} {array_struct_type};\n\n"

                register_struct += f"  {array_struct_type} {register_object.name}[{register_object.length}];\n"
        register_struct += f"}} {register_struct_type};\n"
        return array_structs + register_struct

    def _register_defines(self, register_objects):
        c_code = f"#define {self.module_name.upper()}_NUM_REGS ({register_objects[-1].index + 1}u)\n\n"

        for register, register_array in self._iterate_registers(register_objects):
            c_code += self._addr_define(register, register_array)
            c_code += self._bit_definitions(register, register_array)
            c_code += "\n"

        return c_code

    def _addr_define(self, register, register_array):
        name = self._register_define_name(register, register_array)
        if register_array is None:
            addr = register.index * 4
            return f"#define {name}_ADDR ({addr}u)\n"

        c_code = f"#define {name}_ADDR(array_index) "\
            f"(4u * ({register_array.base_index}u + (array_index) * {len(register_array.registers)}u + {register.index}u))\n"
        return c_code

    def _bit_definitions(self, register, register_array):
        register_name = self._register_define_name(register, register_array)

        c_code = ""
        for bit in register.bits:
            bit_name = f"{register_name}_{bit.name.upper()}"
            c_code += f"#define {bit_name}_BIT ({bit.index}u)\n"
            c_code += f"#define {bit_name} ({2**bit.index}u)\n"

        return c_code

    def _register_define_name(self, register, register_array):
        if register_array is None:
            name = f"{self.module_name}_{register.name}"
        else:
            name = f"{self.module_name}_{register_array.name}_{register.name}"
        return name.upper()

    def _constants(self, constants):
        c_code = ""
        for constant in constants:
            c_code += f"#define {self.module_name.upper()}_CONSTANT_{constant.name.upper()} ({constant.value})\n"
        return c_code
