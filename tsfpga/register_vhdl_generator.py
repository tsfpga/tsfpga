# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class RegisterVhdlGenerator:

    def __init__(self, register_list):
        self.register_list = register_list

    @staticmethod
    def _comment(comment):
        return f"-- {comment}\n"

    def _header(self):
        vhdl = self._comment(self.register_list.generated_info())
        return vhdl

    def _register_constant_name(self, register):
        return self.register_list.name + "_" + register.name

    def _register_indexes(self):
        vhdl = ""
        for register in self.register_list.iterate_registers():
            constant = self._register_constant_name(register)
            vhdl += f"  constant {constant} : integer := {register.idx};\n"

        return vhdl

    def _register_map(self):
        num_regs = str(len(self.register_list.registers))
        map_name = self.register_list.name + "_reg_map"

        register_definitions = []
        for register in self.register_list.iterate_registers():
            constant = self._register_constant_name(register)
            mode = register.mode
            register_definitions.append(f"  (idx => {constant}, reg_type => {mode})")

        vhdl = f"  constant {map_name} : reg_definition_vec_t(0 to {num_regs} - 1) := (\n  "
        vhdl += ",\n  ".join(register_definitions)
        vhdl += "\n  );\n"
        vhdl += "\n"
        vhdl += f"  subtype {self.register_list.name}_regs_t is reg_vec_t({map_name}'range);\n"
        vhdl += f"  constant {self.register_list.name}_regs_zero : \
{self.register_list.name}_regs_t := (others => (others => '0'));\n"
        vhdl += f"  subtype {self.register_list.name}_reg_was_written_t is std_logic_vector({map_name}'range);\n"
        return vhdl

    def _register_bits(self):
        vhdl = ""
        for register in self.register_list.iterate_registers():
            for bit in register.bits:
                name = self._register_constant_name(register) + "_" + bit.name
                vhdl += f"  constant {name} : integer := {bit.idx};\n"
            if register.bits:
                vhdl += "\n"

        return vhdl

    def get_package(self):
        pkg_name = self.register_list.name + "_regs_pkg"

        vhdl = f"""
{self._header()}

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library reg_file;
use reg_file.reg_file_pkg.all;


package {pkg_name} is

{self._register_indexes()}
{self._register_map()}
{self._register_bits()}
end;"""

        return vhdl
