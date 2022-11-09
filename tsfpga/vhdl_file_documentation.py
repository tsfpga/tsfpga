# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import re

# First party libraries
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

        This implementation uses some regular expressions to find the generics and ports and modify
        them.
        The use of regular expressions makes it somewhat simple but also limited.
        Comments in strange places, specifically the string ``port (`` in a comment will make the
        mechanism fail.
        Also an entity with generics but no ports will be falsely interpreted as only ports.

        These known limitations do not pose any known practical problem and are hence considered
        worth it in order to keep the implementation simple.
        The real solution would be to fix upstream in symbolator and hdlparse.

        Return:
            str: VHDL ``component`` declaration. ``None`` if file is a package, and hence contains
            no ``entity``.
        """
        if self._vhd_file_path.name.endswith("_pkg.vhd"):
            # File is a package, hence contains no entity
            return None

        entity_name = self._vhd_file_path.stem
        entity_regexp = re.compile(
            rf"entity\s+{entity_name}\s+is"
            # Match all the code for generics and ports.
            # Is non-greedy, so it will only match up until the "end" declaration below.
            # Generic block optionally
            r"\s*(.+?)\s*(\)\s*;\s*)?"
            # Port block
            r"port\s*\(\s*(.+?)\s*"
            #
            r"\)\s*;\s*"
            # Shall be able to handle
            #   end entity;
            #   end entity <name>;
            #   end <name>;
            #   end;
            # with different whitespace around.
            rf"end(\s+entity|\s+entity\s+{entity_name}|\s+{entity_name}|)\s*;",
            re.IGNORECASE | re.DOTALL,
        )

        file_contents = read_file(self._vhd_file_path)

        match = entity_regexp.search(file_contents)
        if match is None:
            return None

        if match.group(2) and match.group(3):
            # Entity declaration contains both generics and ports
            generics = match.group(1)
        else:
            # Only one match, which we assume is ports (generics only is not supported)
            generics = None

        ports = match.group(3)

        # Remove default values.
        # Symbolator stops parsing if it encounters vector default values (others => ...).
        default_value_regexp = re.compile(r"\s*:=.+?(;|$)", re.IGNORECASE | re.DOTALL)

        # Replace the assignment with only the ending character (";" or "")
        def default_value_replace(match):
            return match.group(1)

        # Remove any vector range declarations in port list.
        # The lines become too long so they don't fit in the image.
        vector_regexp = re.compile(r"\([^;\n]+\)", re.IGNORECASE)

        if generics:
            generics = default_value_regexp.sub(repl=default_value_replace, string=generics)
            generics = vector_regexp.sub(repl="", string=generics)

        ports = default_value_regexp.sub(repl=default_value_replace, string=ports)
        ports = vector_regexp.sub(repl="", string=ports)

        if generics:
            generics_code = f"  {generics}\n  );\n"
        else:
            generics_code = ""

        ports_code = f"  port (\n    {ports}\n  );"

        component = f"""\
component {entity_name} is
{generics_code}{ports_code}
end component;"""

        return component
