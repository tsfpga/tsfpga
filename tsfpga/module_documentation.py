# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from tsfpga.system_utils import create_file, read_file
from tsfpga.vhdl_file_documentation import VhdlFileDocumentation


class ModuleDocumentation:

    """
    Methods for generating a reStructuredText document with module documentation.
    The content is extracted from VHDL source file headers.
    """

    def __init__(self, module):
        """
        Arguments:
            module (:class:`.BaseModule`): The module which shall be documented.
        """
        self._module = module

    def get_overview_rst(self):
        """
        Get the contents of the module's ``doc/<name>.rst``, i.e. the module "overview" document.

        Return:
            str: Module overview RST. ``None`` if file does not exist.
        """
        overview_rst_file = self._module.path / "doc" / f"{self._module.name}.rst"
        if overview_rst_file.exists():
            return read_file(overview_rst_file)

        return None

    def get_register_rst(self, heading_character):
        """
        Get an RST snippet with a link to the module's register documentation, if available.
        Note that this will create an RST ``:download:`` statement to the register .html page.
        When building, the ``.html`` file must be present in the same directory as the
        ``.rst`` file.
        This is done automatically by :meth:`.create_rst_document`.

        Arguments:
            heading_character (str): Character to use for heading underline.

        Return:
            str: RST snippet with link to register HTML. ``None`` if module does not have registers.
        """
        if self._module.registers is not None:
            heading = "Register interface"
            heading_underline = heading_character * len(heading)
            return f"""\
.. _{self._module.name}.register_interface:

{heading}
{heading_underline}

This module has register definitions.
Please see :download:`separate HTML page <{self._module.name}_regs.html>` for \
register documentation.
"""

        return None

    def get_submodule_rst(self, heading_character, exclude_files=None):
        """
        Get RST code with documentation of the different sub-modules (files) of the module.
        Contains documentation that is extracted from the file headers, as well as a
        symbolator symbol of the entity.

        Arguments:
            heading_character (str): Character to use for heading underline.

        Return:
            str: RST code with sub-module documentation.
        """
        exclude_files = {} if exclude_files is None else exclude_files

        rst = ""

        for hdl_file in self._get_vhdl_files(exclude_files):
            vhdl_file_path = hdl_file.path

            vhdl_file_documentation = VhdlFileDocumentation(vhdl_file_path)

            file_rst = vhdl_file_documentation.get_header_rst()
            file_rst = "" if file_rst is None else file_rst

            symbolator_rst = self._get_symbolator_rst(vhdl_file_documentation)
            symbolator_rst = "" if symbolator_rst is None else symbolator_rst

            entity_name = vhdl_file_path.stem
            heading = f"{vhdl_file_path.name}"
            heading_underline = heading_character * len(heading)
            rst += f"""
.. _{self._module.name}.{entity_name}:

{heading}
{heading_underline}

{symbolator_rst}

{file_rst}
"""

        return rst

    def get_rst_document(self):
        """
        Get a complete RST document with the content of :meth:`.get_overview_rst`,
        :meth:`.get_register_rst`, and :meth:`.get_submodule_rst`, as well as a top level heading.

        Returns:
            str: An RST document.
        """
        heading_character_1 = "="
        heading_character_2 = "-"

        heading = f"Module {self._module.name}"
        heading_underline = heading_character_1 * len(heading)

        overview_rst = self.get_overview_rst()
        overview_rst = "" if overview_rst is None else overview_rst

        registers_rst = self.get_register_rst(heading_character=heading_character_2)
        registers_rst = "" if registers_rst is None else registers_rst

        submodule_rst = self.get_submodule_rst(heading_character=heading_character_2)

        rst = f"""\

.. _module_{self._module.name}:

{heading}
{heading_underline}

This document contains technical documentation for the ``{self._module.name}`` module.

{overview_rst}

{registers_rst}

{submodule_rst}
"""

        return rst

    def create_rst_document(self, output_path):
        """
        Create an ``.rst`` file in ``output_path`` with the content from :meth:`.get_rst_document`.
        If the module has registers, the HTML page will also be generated in ``output_path``, so
        that e.g. sphinx can be run directly.

        Arguments:
            output_path (pathlib.Path): Document will be placed here.
        """
        register_list = self._module.registers
        if register_list is not None:
            register_list.create_html_page(output_path)

        create_file(output_path / f"{self._module.name}.rst", contents=self.get_rst_document())

    def _get_vhdl_files(self, exclude_files):
        """
        Get VHDL files that shall be included in the documentation, in order.
        """
        hdl_files = self._module.get_synthesis_files(files_avoid=exclude_files)

        module_regs_pkg = self._module.path / f"{self._module.name}_regs_pkg.vhd"
        vhdl_files = []
        for hdl_file in hdl_files:
            if hdl_file.is_vhdl and hdl_file.path != module_regs_pkg:
                vhdl_files.append(hdl_file)

        # Sort by file name
        def sort_key(vhdl_file):
            return vhdl_file.path.name

        vhdl_files = sorted(vhdl_files, key=sort_key)

        return vhdl_files

    @staticmethod
    def _get_symbolator_rst(vhdl_file_documentation):
        """
        Get RST for rendering a symbolator component.
        """
        component = vhdl_file_documentation.get_symbolator_component()
        if component is None:
            return ""

        indent = "  "
        rst = ".. symbolator::\n\n"
        rst += indent + component.replace("\n", f"\n{indent}")

        return rst
