# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# First party libraries
from tsfpga.system_utils import create_file, file_is_in_directory, read_file
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

    def get_submodule_rst(
        self,
        heading_character,
        heading_character_2,
        exclude_files=None,
        exclude_module_folders=None,
    ):
        """
        Get RST code with documentation of the different sub-modules (files) of the module.
        Contains documentation that is extracted from the file headers, as well as a
        symbolator symbol of the entity.

        Arguments:
            heading_character (str): Character to use for heading underline.
            heading_character_2 (str): Character to use for next level of heading underline.
            exclude_files (set(pathlib.Path)): Files that shall be excluded from the documentation.
            exclude_module_folders (list(str)): Folder names within the module root that shall be
                excluded from documentation. For example, if you chosen module structure places
                only netlist build wrappers in the "rtl/" folder within modules, and you do not
                want them included in the documentation, then pass the argument ["rtl"].

        Return:
            str: RST code with sub-module documentation.
        """
        exclude_module_folders = [] if exclude_module_folders is None else exclude_module_folders
        exclude_module_paths = [self._module.path / name for name in exclude_module_folders]

        all_builds = self._module.get_build_projects()

        rst = ""

        for hdl_file in self._get_vhdl_files(
            exclude_files=exclude_files, exclude_folders=exclude_module_paths
        ):
            vhdl_file_path = hdl_file.path
            netlist_build_base_name = f"{self._module.library_name}.{vhdl_file_path.stem}"

            netlist_builds = []
            # Include all netlist builds whose project name matches this file
            for project in all_builds:
                if project.is_netlist_build and (
                    project.name == netlist_build_base_name
                    or project.name.startswith(f"{netlist_build_base_name}.")
                ):
                    netlist_builds.append(project)

            rst += self._get_vhdl_file_rst(
                vhdl_file_path=vhdl_file_path,
                heading_character=heading_character,
                heading_character_2=heading_character_2,
                netlist_builds=netlist_builds,
            )

        return rst

    def get_rst_document(self, exclude_module_folders=None):
        """
        Get a complete RST document with the content of :meth:`.get_overview_rst`,
        :meth:`.get_register_rst`, and :meth:`.get_submodule_rst`, as well as a top level heading.

        Arguments:
            exclude_module_folders (list(str)): Folder names within the module root that shall be
                excluded from documentation.

        Returns:
            str: An RST document.
        """
        heading_character_1 = "="
        heading_character_2 = "-"
        heading_character_3 = "_"

        heading = f"Module {self._module.name}"
        heading_underline = heading_character_1 * len(heading)

        overview_rst = self.get_overview_rst()
        overview_rst = "" if overview_rst is None else overview_rst

        registers_rst = self.get_register_rst(heading_character=heading_character_2)
        registers_rst = "" if registers_rst is None else registers_rst

        submodule_rst = self.get_submodule_rst(
            heading_character=heading_character_2,
            heading_character_2=heading_character_3,
            exclude_module_folders=exclude_module_folders,
        )

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

    def create_rst_document(self, output_path, exclude_module_folders=None):
        """
        Create an ``.rst`` file in ``output_path`` with the content from :meth:`.get_rst_document`.
        If the module has registers, the HTML page will also be generated in ``output_path``, so
        that e.g. sphinx can be run directly.

        Arguments:
            output_path (pathlib.Path): Document will be placed here.
            exclude_module_folders (list(str)): Folder names within the module root that shall be
                excluded from documentation.
        """
        register_list = self._module.registers
        if register_list is not None:
            register_list.create_html_page(output_path)

        rst = self.get_rst_document(exclude_module_folders=exclude_module_folders)
        create_file(output_path / f"{self._module.name}.rst", contents=rst)

    def _get_vhdl_files(self, exclude_files, exclude_folders):
        """
        Get VHDL files that shall be included in the documentation, in order.
        """
        hdl_files = self._module.get_documentation_files(files_avoid=exclude_files)

        module_regs_pkg = self._module.path / f"{self._module.name}_regs_pkg.vhd"

        def file_should_be_included(hdl_file):
            if file_is_in_directory(hdl_file.path, exclude_folders):
                return False

            if not hdl_file.is_vhdl:
                return False

            if hdl_file.path == module_regs_pkg:
                return False

            return True

        vhdl_files = [hdl_file for hdl_file in hdl_files if file_should_be_included(hdl_file)]

        # Sort by file name
        def sort_key(vhdl_file):
            return vhdl_file.path.name

        vhdl_files = sorted(vhdl_files, key=sort_key)

        return vhdl_files

    def _get_vhdl_file_rst(
        self, vhdl_file_path, heading_character, heading_character_2, netlist_builds
    ):
        """
        Get reStructuredText documentation for a VHDL file.
        """
        vhdl_file_documentation = VhdlFileDocumentation(vhdl_file_path)

        file_rst = vhdl_file_documentation.get_header_rst()
        file_rst = "" if file_rst is None else file_rst

        symbolator_rst = self._get_symbolator_rst(vhdl_file_documentation)
        symbolator_rst = "" if symbolator_rst is None else symbolator_rst

        resource_utilization_rst = self._get_resource_utilization_rst(
            vhdl_file_path=vhdl_file_path,
            heading_character=heading_character_2,
            netlist_builds=netlist_builds,
        )

        entity_name = vhdl_file_path.stem
        heading = f"{vhdl_file_path.name}"
        heading_underline = heading_character * len(heading)

        rst = f"""
.. _{self._module.name}.{entity_name}:

{heading}
{heading_underline}

{symbolator_rst}

{file_rst}

{resource_utilization_rst}
"""

        return rst

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

    def _get_resource_utilization_rst(
        self,
        vhdl_file_path,
        heading_character,
        netlist_builds,
    ):  # pylint: disable=too-many-locals,too-many-branches
        # First, loop over all netlist builds for this module and assemble information
        generics = []
        checkers = []
        for netlist_build in netlist_builds:
            if netlist_build.build_result_checkers:
                generics.append(netlist_build.static_generics)

                # Create a dictionary for each build, that maps "Checker name": "value"
                checker_dict = {}
                for checker in netlist_build.build_result_checkers:
                    # Casting the limit to string yields e.g. "< 4", "4" or "> 4"
                    checker_dict[checker.name] = str(checker.limit)

                checkers.append(checker_dict)

        # Make RST of the information
        rst = ""
        if generics:
            heading = "Resource utilization"
            heading_underline = heading_character * len(heading)
            rst = f"""
{heading}
{heading_underline}

This entity has `netlist builds <https://tsfpga.com/netlist_build.html>`__ set up with
`automatic size checkers <https://tsfpga.com/netlist_build.html#build-result-checkers>`__
in ``module_{self._module.name}.py``.
The following table lists the resource utilization for the entity, depending on
generic configuration.

.. list-table:: Resource utilization for {vhdl_file_path.name} netlist builds.
  :header-rows: 1

"""

            # Make a list of the unique checker names. Use list rather than set to preserve order.
            checker_names = []
            for build_checkers in checkers:
                for checker_name in build_checkers:
                    if checker_name not in checker_names:
                        checker_names.append(checker_name)

            # Fill in the header row
            rst += "  * - Generics\n"
            for checker_name in checker_names:
                rst += f"    - {checker_name}\n"

            # Make one row for each netlist build
            for build_idx, generic_dict in enumerate(generics):
                generic_strings = [f"{name} = {value}" for name, value in generic_dict.items()]
                generics_rst = "\n\n      ".join(generic_strings)

                rst += f"""\
  * - {generics_rst}"""

                # If the "top" of the project is different than this file name, we assume that it
                # is a wrapper. Add a note to the table about this. This occurs e.g. in the reg_file
                # and fifo modules.
                if netlist_builds[build_idx].top != vhdl_file_path.stem:
                    if generic_strings:
                        # If there is already something in the generic column, this note shall be
                        # placed on a new line.
                        leader = "\n\n      "
                    else:
                        # Otherwise, i.e. if the netlist build has no generics set,
                        # the note shall be placed as the first thing. This is the case with
                        # two builds in the reg_file module.
                        leader = ""

                    rst += f"""\
{leader}(Using wrapper

      {netlist_builds[build_idx].top}.vhd)"""

                rst += "\n"

                for checker_name in checker_names:
                    checker_value = checkers[build_idx][checker_name]
                    rst += f"    - {checker_value}\n"

        return rst
