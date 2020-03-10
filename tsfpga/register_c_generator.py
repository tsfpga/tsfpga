# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class RegisterCGenerator:

    def __init__(self, module_name, generated_info):
        self.module_name = module_name
        self.generated_info = generated_info

    @staticmethod
    def _comment(comment):
        return f"/* {comment} */\n"

    def _header(self):
        return self._comment(self.generated_info)

    def _register_struct(self, registers):
        c_code = f"struct {self.module_name}_regs_t {{\n"
        for register in registers:
            c_code += f"  uint32_t {register.name};\n"
        c_code += "};\n"
        return c_code

    def _register_bits(self, registers):
        c_code = ""
        for register in registers:
            for bit in register.bits:
                bit_name = (self.module_name + "_" + register.name + "_" + bit.name).upper()
                c_code += f"#define {bit_name}_BIT ({bit.idx}uL)\n"
                c_code += f"#define {bit_name}     ({2**bit.idx}uL)\n"
                c_code += "\n"

        return c_code

    def get_header(self, registers):
        define_name = self.module_name.upper() + "_REGS_H"

        c_code = f"""
{self._header()}

#ifndef {define_name}
#define {define_name}
#pragma pack(push, 1)

#include <stdint.h>

{self._register_struct(registers)}
{self._register_bits(registers)}

#pragma pack(pop)
#endif {self._comment(define_name)}"""

        return c_code
