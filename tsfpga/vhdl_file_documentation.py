# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import re

from tsfpga.system_utils import read_file
from tsfpga.test.lint.test_copyright import CopyrightHeader


VHDL_COMMENT_SEPARATOR = "-- " + ("-" * (CopyrightHeader.separator_line_length - 3))


class VhdlFileDocumentation:

    """
    Methods to extract documentation from a VHDL source file.
    """

    def __init__(self, vhd_file_path):
        """
        Arguments:
            vhd_file_path (pathlib.Path): Path to the VHDL file which shall be documented.
        """
        self._vhd_file_path = vhd_file_path

    def get_header_rst(self):
        """
        Get the contents of the VHDL file's header. This means everything that is in the comment
        block at the start of the file, after the copyright notice.

        Return:
            str: File header content.
        """
        file_contents = read_file(self._vhd_file_path)

        documentation_header_regexp = re.compile(
            VHDL_COMMENT_SEPARATOR
            + r"\n(.+?)\n"
            + VHDL_COMMENT_SEPARATOR
            + r"\n(.+?)\n"
            + VHDL_COMMENT_SEPARATOR
            + r"\n\n",
            re.DOTALL,
        )
        match = documentation_header_regexp.search(file_contents)
        if match is None:
            return None

        # The first group will match the copyright header. Second group is documentation.
        lines = match.group(2).split("\n")
        text = ""
        for line in lines:
            if line == "--":
                text += "\n"
            else:
                # Remove initial "-- " from comments
                text += f"{line[3:]}\n"

        return text

    def get_symbolator_component(self):
        """
        Return a string with a ``component`` declaration equivalent to the ``entity`` declaration
        within the file. (We use entity's but symbolator requires component's).

        Default values and range declarations on ports are removed since symbolator does not seem
        to handle them.

        Return:
            str: VHDL ``component`` declaration. ``None`` if file is a package, and hence contains
            no ``entity``.
        """
        if self._vhd_file_path.name.endswith("_pkg.vhd"):
            # File is a package
            return None

        entity_name = self._vhd_file_path.stem
        entity_regexp = re.compile(
            f"entity {entity_name} is" + r"\n(.+?)end entity;", re.IGNORECASE | re.DOTALL
        )

        file_contents = read_file(self._vhd_file_path)
        match = entity_regexp.search(file_contents)
        if match is None:
            return None

        component = f"component {entity_name} is\n{match.group(1)}end component;"

        # Remove default values.
        # Symbolator stops parsing if it encounters vector default values (others => ...).
        default_value_regexp = re.compile(r"\s+:=\s+[^;\n]+", re.IGNORECASE)
        component = default_value_regexp.sub("", component)

        # Remove any vector range declarations in port list.
        # The lines become too long so they don't fit in the image.
        vector_regexp = re.compile(r"\([^;\n]+\)", re.IGNORECASE)
        component = vector_regexp.sub("", component)

        return component
