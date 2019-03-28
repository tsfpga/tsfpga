# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class RegisterCGenerator:

    def __init__(self, register_list):
        self.register_list = register_list

    @staticmethod
    def _comment(comment):
        return f"/* {comment} */\n"

    def _header(self):
        c_code = self._comment(self.register_list.generated_info())
        c_code += self._comment(self.register_list.generated_source_info())
        return c_code

    def _register_struct(self):
        c_code = f"struct {self.register_list.name}_regs_t {{\n"
        for register in self.register_list.iterate_registers():
            c_code += f"  uint32_t {register.name};\n"
        c_code += "};\n"
        return c_code

    def _register_bits(self):
        c_code = ""
        for register in self.register_list.iterate_registers():
            for bit in register.bits:
                bit_name = (self.register_list.name + "_" + register.name + "_" + bit.name).upper()
                c_code += f"#define {bit_name}_BIT ({bit.idx}uL)\n"
                c_code += f"#define {bit_name}     ({2**bit.idx}uL)\n"
                c_code += "\n"

        return c_code

    def get_header(self):
        define_name = self.register_list.name.upper() + "_REGS_H"

        c_code = f"""
{self._header()}

#ifndef {define_name}
#define {define_name}
#pragma pack(push, 1)

#include <stdint.h>

{self._register_struct()}
{self._register_bits()}

#pragma pack(pop)
#endif {self._comment(define_name)}"""

        return c_code
