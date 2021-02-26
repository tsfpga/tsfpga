# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from .register import Register, REGISTER_MODES
from .html_translator import HtmlTranslator


class RegisterHtmlGenerator:
    """
    Generate a HTML page with register information.
    """

    def __init__(self, module_name, generated_info):
        self.module_name = module_name
        self.generated_info = generated_info
        self._html_translator = HtmlTranslator()

    def get_register_table(self, register_objects):
        html = self._file_header()
        html += self._get_register_table(register_objects)
        return html

    def get_constant_table(self, constants):
        if not constants:
            return ""

        html = self._file_header()
        html += self._get_constant_table(constants)
        return html

    def get_page(
        self, register_objects, constants, table_style=None, font_style=None, extra_style=""
    ):
        title = f"Documentation of {self.module_name} registers"

        if font_style is None:
            font_style = """
html * {
  font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
}"""

        if table_style is None:
            table_style = """
table {
  border-collapse: collapse;
}
td, th {
  border: 1px solid #ddd;
  padding: 8px;
}
td.array_header {
  background-color: #4cacaf;
  color: white;
}
tr:nth-child(even) {
  background-color: #f2f2f2;
}
th {
  padding-top: 12px;
  padding-bottom: 12px;
  text-align: left;
  background-color: #4CAF50;
  color: white;
}"""

        html = f"""\
{self._file_header()}

<!DOCTYPE html>
<html>
<head>
  <title>{title}</title>
  <style>
{font_style}
{table_style}
{extra_style}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>This document is a specification for the register interface of the FPGA module \
<b>{self.module_name}</b>.</p>
  <p>{' '.join(self.generated_info)}</p>
  <h2>Register modes</h2>
  <p>The following register modes are available.</p>
{self._get_mode_descriptions()}
  <h2>Registers</h2>
  <p>The following registers make up the register map.</p>
{self._get_register_table(register_objects)}
"""

        if constants:
            html += f"""
  <h2>Constants</h2>
  <p>The following constants are part of the register interface.</p>
{self._get_constant_table(constants)}"""

        html += """
</body>
</html>"""

        return html

    @staticmethod
    def _comment(comment):
        return f"<!-- {comment} -->\n"

    def _file_header(self):
        return "".join([self._comment(header_line) for header_line in self.generated_info])

    @staticmethod
    def _to_hex_string(value, num_nibbles=4):
        if value < 0:
            return "N/A"

        formatting_string = "0x{:0%iX}" % num_nibbles
        return formatting_string.format(value)

    def _annotate_register(self, register, register_array_index=None, array_index_increment=None):
        if register_array_index is None:
            address_readable = self._to_hex_string(register.address)
            index = register.address // 4
        else:
            register_address = self._to_hex_string(4 * register_array_index)
            address_increment = self._to_hex_string(4 * array_index_increment)
            address_readable = f"{register_address} + i &times; {address_increment}"

            index = f"{register_array_index} + i &times; {array_index_increment}"

        description = self._html_translator.translate(register.description)
        html = f"""
  <tr>
    <td><strong>{register.name}</strong></td>
    <td>{index}</td>
    <td>{address_readable}</td>
    <td>{REGISTER_MODES[register.mode].mode_readable}</td>
    <td>{register.default_value}</td>
    <td>{description}</td>
  </tr>"""

        return html

    def _annotate_bit(self, bit):
        description = self._html_translator.translate(bit.description)
        html = f"""
  <tr>
    <td>&nbsp;&nbsp;<em>{bit.name}</em></td>
    <td>&nbsp;&nbsp;{bit.index}</td>
    <td></td>
    <td></td>
    <td></td>
    <td>{description}</td>
  </tr>"""

        return html

    def _get_register_table(self, register_objects):
        html = """
<table>
<thead>
  <tr>
    <th>Name</th>
    <th>Index</th>
    <th>Address</th>
    <th>Mode</th>
    <th>Default value</th>
    <th>Description</th>
  </tr>
</thead>
<tbody>"""

        for register_object in register_objects:
            if isinstance(register_object, Register):
                html += self._annotate_register(register_object)
                for bit in register_object.bits:
                    html += self._annotate_bit(bit)
            else:
                html += f"""
  <tr>
    <td colspan="6" class="array_header">
      Register array <strong>{register_object.name}</strong>, \
repeated {register_object.length} times
    </td>
  </tr>"""
                array_index_increment = len(register_object.registers)
                for register in register_object.registers:
                    register_index = register_object.base_index + register.index
                    html += self._annotate_register(register, register_index, array_index_increment)
                    for bit in register.bits:
                        html += self._annotate_bit(bit)
                html += f"""
  <tr>
    <td colspan="6" class="array_header">
      End register array <strong>{register_object.name}</strong>
    </td>
  </tr>"""

        html += """
</tbody>
</table>"""

        return html

    def _get_constant_table(self, constants):
        html = """
<table>
<thead>
  <tr>
    <th>Name</th>
    <th>Value (decimal)</th>
    <th>Value (hexadecimal)</th>
    <th>Description</th>
  </tr>
</thead>
<tbody>"""

        for constant in constants:
            description = self._html_translator.translate(constant.description)
            html += f"""
  <tr>
    <td><strong>{constant.name}</strong></td>
    <td>{constant.value}</td>
    <td>{self._to_hex_string(constant.value, num_nibbles=8)}</td>
    <td>{description}</td>
  </tr>"""

        html += """
</tbody>
</table>"""
        return html

    @staticmethod
    def _get_mode_descriptions():
        html = """
<table>
<thead>
  <tr>
    <th>Mode</th>
    <th>Description</th>
  </tr>
</thead>
<tbody>"""

        for mode in REGISTER_MODES.values():
            html += f"""
<tr>
  <td>{mode.mode_readable}</td>
  <td>{mode.description}</td>
</tr>
"""
        html += """
</tbody>
</table>"""
        return html
