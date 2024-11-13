# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path
from typing import TYPE_CHECKING, Optional

# Third party libraries
from hdl_registers.generator.html.page import HtmlPageGenerator

# Local folder libraries
from .about import WEBSITE_URL
from .system_utils import create_file, file_is_in_directory, read_file
from .vhdl_file_documentation import VhdlFileDocumentation
from .vivado.project import VivadoNetlistProject

if TYPE_CHECKING:
    # Local folder libraries
    from .hdl_file import HdlFile
    from .module import BaseModule


class ModuleDocumentation:
    """
    Methods for generating a reStructuredText document with module documentation.
    The content is extracted from VHDL source file headers.
    """

    def __init__(
        self,
        module: "BaseModule",
        repository_url: Optional[str] = None,
        repository_name: Optional[str] = None,
    ) -> None:
        """
        Arguments:
            module: The module which shall be documented.
            repository_url: Optionally specify an URL where the source code can be viewed.
                If this argument is specified, links will be added to the documentation.
                URL should be to the module folder within the repository.
            repository_name: Optionally specify the name of the repository URL.
                For example "GitLab".
        """
        self._module = module
        self._repository_url = repository_url
        self._repository_name = repository_name

        assert (repository_url is None) == (
            repository_name is None
        ), "Both or none of the repository arguments must be set"

    def get_overview_rst(self) -> Optional[str]:
        """
        Get the contents of the module's ``doc/<name>.rst``, i.e. the module "overview" document.

        Return:
            Module overview RST. ``None`` if file does not exist.
        """
        overview_rst_file = self._module.path / "doc" / f"{self._module.name}.rst"
        if overview_rst_file.exists():
            return read_file(overview_rst_file)

        return None

    def get_register_rst(self, heading_character: str) -> Optional[str]:
        """
        Get an RST snippet with a link to the module's register documentation, if available.
        Note that this will create an RST ``:download:`` statement to the register .html page.
        When building, the ``.html`` file must be present in the same directory as the
        ``.rst`` file.
        This is done automatically by :meth:`.create_rst_document`.

        Arguments:
            heading_character: Character to use for heading underline.

        Return:
            RST snippet with link to register HTML. ``None`` if module does not have registers.
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
        heading_character: str,
        heading_character_2: str,
        exclude_files: Optional[set[Path]] = None,
        exclude_module_folders: Optional[list[str]] = None,
    ) -> str:
        """
        Get RST code with documentation of the different sub-modules (files) of the module.
        Contains documentation that is extracted from the file headers, as well as a
        symbolator symbol of the entity.

        Arguments:
            heading_character: Character to use for heading underline.
            heading_character_2: Character to use for next level of heading underline.
            exclude_files: Files that shall be excluded from the documentation.
            exclude_module_folders: Folder names within the module root that shall be
                excluded from documentation. For example, if you chosen module structure places
                only netlist build wrappers in the "rtl/" folder within modules, and you do not
                want them included in the documentation, then pass the argument ["rtl"].

        Return:
            RST code with sub-module documentation.
        """
        exclude_module_folders = [] if exclude_module_folders is None else exclude_module_folders
        exclude_module_paths = [self._module.path / name for name in exclude_module_folders]

        all_builds = self._module.get_build_projects()

        rst = ""

        for vhdl_file_path in self._get_vhdl_files(
            exclude_files=exclude_files, exclude_folders=exclude_module_paths
        ):
            netlist_build_base_name = f"{self._module.library_name}.{vhdl_file_path.stem}"

            netlist_builds = []
            # Include all netlist builds whose project name matches this file
            for project in all_builds:
                if isinstance(project, VivadoNetlistProject) and (
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

    def get_rst_document(self, exclude_module_folders: Optional[list[str]] = None) -> str:
        """
        Get a complete RST document with the content of :meth:`.get_overview_rst`,
        :meth:`.get_register_rst`, and :meth:`.get_submodule_rst`, as well as a top level heading.

        Arguments:
            exclude_module_folders: Folder names within the module root that shall be
                excluded from documentation.

        Return:
            An RST document.
        """
        heading_character_1 = "="
        heading_character_2 = "-"
        heading_character_3 = "_"

        heading = f"Module {self._module.name}"
        heading_underline = heading_character_1 * len(heading)

        if self._module.registers is not None:
            register_note_rst = (
                "This module has a register interface, so make sure to study the "
                f":ref:`register interface documentation <{self._module.name}.register_interface>` "
                "as well as this top-level document.\n"
            )
        else:
            register_note_rst = ""

        if self._repository_url:
            url_rst = (
                f"To browse the source code, visit the "
                f"`repository on {self._repository_name} <{self._repository_url}>`__.\n"
            )
        else:
            url_rst = ""

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
{register_note_rst}\
{url_rst}\

{overview_rst}

{registers_rst}

{submodule_rst}
"""

        return rst

    def create_rst_document(
        self, output_path: Path, exclude_module_folders: Optional[list[str]] = None
    ) -> None:
        """
        Create an ``.rst`` file in ``output_path`` with the content from :meth:`.get_rst_document`.
        If the module has registers, the HTML page will also be generated in ``output_path``, so
        that e.g. sphinx can be run directly.

        Arguments:
            output_path: Document will be placed here.
            exclude_module_folders: Folder names within the module root that shall be
                excluded from documentation.
        """
        register_list = self._module.registers
        if register_list is not None:
            HtmlPageGenerator(register_list=register_list, output_folder=output_path).create()

        rst = self.get_rst_document(exclude_module_folders=exclude_module_folders)
        create_file(output_path / f"{self._module.name}.rst", contents=rst)

    def _get_vhdl_files(
        self, exclude_files: Optional[set[Path]], exclude_folders: list[Path]
    ) -> list[Path]:
        """
        Get VHDL files that shall be included in the documentation, in order.
        """
        # Exclude all file types except VHDL.
        hdl_files = self._module.get_documentation_files(
            files_avoid=exclude_files, include_verilog=False, include_systemverilog=False
        )

        def file_should_be_included(hdl_file: "HdlFile") -> bool:
            if file_is_in_directory(hdl_file.path, exclude_folders):
                return False

            return True

        vhdl_file_paths = [
            hdl_file.path for hdl_file in hdl_files if file_should_be_included(hdl_file)
        ]

        # Sort by file name
        def sort_key(path: Path) -> str:
            return path.name

        vhdl_files = sorted(vhdl_file_paths, key=sort_key)

        return vhdl_files

    def _get_vhdl_file_rst(
        self,
        vhdl_file_path: Path,
        heading_character: str,
        heading_character_2: str,
        netlist_builds: list["VivadoNetlistProject"],
    ) -> str:
        """
        Get reStructuredText documentation for a VHDL file.
        """
        vhdl_file_documentation = VhdlFileDocumentation(vhdl_file_path)

        file_rst = vhdl_file_documentation.get_header_rst()
        file_rst = "" if file_rst is None else file_rst

        if self._repository_url:
            url_rst = (
                f"`View source code on {self._repository_name} "
                f"<{self._repository_url}/{vhdl_file_path.relative_to(self._module.path)}>`__."
            )
        else:
            url_rst = ""

        symbolator_rst = self._get_symbolator_rst(vhdl_file_documentation)
        symbolator_rst = "" if symbolator_rst is None else symbolator_rst

        entity_name = vhdl_file_path.stem

        resource_utilization_rst = self._get_resource_utilization_rst(
            entity_name=entity_name,
            heading_character=heading_character_2,
            netlist_builds=netlist_builds,
        )

        heading = f"{vhdl_file_path.name}"
        heading_underline = heading_character * len(heading)

        rst = f"""
.. _{self._module.name}.{entity_name}:

{heading}
{heading_underline}

{url_rst}

{symbolator_rst}

{file_rst}

{resource_utilization_rst}
"""

        return rst

    @staticmethod
    def _get_symbolator_rst(vhdl_file_documentation: VhdlFileDocumentation) -> str:
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

    def _get_resource_utilization_rst(  # pylint: disable=too-many-locals,too-many-branches
        self, entity_name: str, heading_character: str, netlist_builds: list["VivadoNetlistProject"]
    ) -> str:
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

            module_py_name = f"module_{self._module.name}.py"
            if self._repository_url:
                module_py_rst = f"`{module_py_name} <{self._repository_url}/{module_py_name}>`__"
            else:
                module_py_rst = f"``{module_py_name}``"

            rst = f"""
.. _{self._module.name}.{entity_name}.resource_utilization:

{heading}
{heading_underline}

This entity has `netlist builds <{WEBSITE_URL}/netlist_build.html>`__ set up with
`automatic size checkers <{WEBSITE_URL}/netlist_build.html#build-result-checkers>`__
in {module_py_rst}.
The following table lists the resource utilization for the entity, depending on
generic configuration.

.. list-table:: Resource utilization for **{entity_name}** netlist builds.
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

                # If the "top" of the project is different than the entity, we assume that it
                # is a wrapper. Add a note to the table about this. This occurs e.g. in the reg_file
                # and fifo modules.
                if netlist_builds[build_idx].top != entity_name:
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
