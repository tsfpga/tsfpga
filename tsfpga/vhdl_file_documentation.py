# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
import re
from pathlib import Path
from typing import Optional

# First party libraries
from tsfpga.system_utils import read_file

SEPARATOR_LINE_LENGTH = 100
VHDL_COMMENT_SEPARATOR = "-- " + ("-" * (SEPARATOR_LINE_LENGTH - 3))


class VhdlFileDocumentation:
    """
    Methods to extract documentation from a VHDL source file.
    """

    def __init__(self, vhd_file_path: Path) -> None:
        """
        Arguments:
            vhd_file_path: Path to the VHDL file which shall be documented.
        """
        self._vhd_file_path = vhd_file_path

    def get_header_rst(self) -> Optional[str]:
        """
        Get the contents of the VHDL file's header. This means everything that is in the comment
        block at the start of the file, after the copyright notice.

        Return:
            File header content.
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

    def get_symbolator_component(  # pylint: disable=too-many-locals,too-many-statements
        self,
    ) -> Optional[str]:
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
            VHDL ``component`` declaration.
            ``None`` if file is a package, and hence contains no ``entity``.
            ``None`` if no ``entity`` is found in the file.
        """
        if self._vhd_file_path.name.endswith("_pkg.vhd"):
            # File is a package, hence contains no entity
            return None

        vhdl = read_file(self._vhd_file_path)

        def replace_comment(match):  # type: ignore
            match_group = match.group(1)
            if (
                match_group
                and match_group.startswith("# {{")
                and match_group.endswith("}}")
                and ";" not in match_group
            ):
                # This is a valid symbolator comment, leave it as is.
                # I.e. "--# {{}}" or "--# {{some text}}
                return f"--{match_group}"

            # Strip comment
            return ""

        # Remove comments so that the remaining VHDL is easier to parse.
        vhdl = re.sub(pattern=r"--(.*)$", repl=replace_comment, string=vhdl, flags=re.MULTILINE)

        # Strip trailing whitespace and empty lines.
        vhdl = re.sub(pattern=r"\s*$", repl="", string=vhdl, flags=re.MULTILINE)

        # Split out the entity declaration from the VHDL file.
        entity_name = self._vhd_file_path.stem
        entity_regexp = re.compile(
            rf"entity\s+{entity_name}\s+is\s+"
            # Match all the code for generics and ports.
            # Is non-greedy, so it will only match up until the "end" declaration below.
            r"(.*?)"
            # Shall be able to handle
            #   end entity;
            #   end entity <name>;
            #   end <name>;
            #   end;
            # with different whitespace around.
            rf"\s*end(\s+entity|\s+entity\s+{entity_name}|\s+{entity_name}|)\s*;",
            re.IGNORECASE | re.DOTALL,
        )

        match = entity_regexp.search(vhdl)
        if match is None or not match.group(1):
            print(f"Found no entity in {self._vhd_file_path}")
            return None

        ports_and_generics = match.group(1)

        # Slit out the generic part and the port part from the entity declaration.
        ports_and_generics_regexp = re.compile(
            # Match all the code for generics and ports.
            # Is non-greedy, so it will only match up until the "end" declaration below.
            # Generic block optionally
            r"\s*(.+?)?\s*(\)\s*;\s*)?"
            # Port block
            r"port\s*\(\s*(.+?)\s*"
            #
            r"\)\s*;\s*$",
            re.IGNORECASE | re.DOTALL,
        )

        match = ports_and_generics_regexp.search(ports_and_generics)
        if match is None:
            print(f"Found no ports or generics in {self._vhd_file_path}")
            return None

        if match.group(2) and match.group(3):
            # Entity declaration contains both generics and ports
            generics = match.group(1)
            assert generics.lower().startswith("generic")

            strip_generics_open = re.compile(r"generic\s*\(", re.IGNORECASE)
            generics = strip_generics_open.sub(repl="", string=generics)
        else:
            # Only one match, which we assume is ports (generics only is not supported)
            generics = None

        ports = match.group(3)

        # Remove default values.
        # Symbolator stops parsing if it encounters vector default values (others => ...).
        default_value_regexp = re.compile(r"\s*:=.+$", re.IGNORECASE | re.DOTALL)

        # Remove any vector range declarations in port/generic list.
        # The lines become too long so they don't fit in the image.
        vector_regexp = re.compile(r"\(.*$", re.IGNORECASE | re.DOTALL)

        def clean_up_declarations(declarations: str) -> str:
            clean_declarations = []

            # Split the list of declarations string into individual.
            # Note that this fails if there are any ";" in comments, so its import that we
            # strip comments before this.
            for declaration in declarations.split(";"):
                cleaned = default_value_regexp.sub(repl="", string=declaration)
                cleaned = vector_regexp.sub(repl="", string=cleaned)

                clean_declarations.append(cleaned)

            return ";".join(clean_declarations)

        if generics:
            generics = clean_up_declarations(generics)

        ports = clean_up_declarations(ports)

        if generics:
            generics_code = f"  generic ({generics}\n  );\n"
        else:
            generics_code = ""

        ports_code = f"  port (\n    {ports}\n  );"

        component = f"""\
component {entity_name} is
{generics_code}{ports_code}
end component;"""

        return component
