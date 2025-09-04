# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import datetime
import platform
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tsfpga import REPO_ROOT
from tsfpga.git_utils import get_git_commit
from tsfpga.vivado.common import get_vivado_version
from tsfpga.vivado.project import VivadoNetlistProject, VivadoProject

if TYPE_CHECKING:
    from hdl_registers.register_list import RegisterList

THIS_DIR = Path(__file__).parent


class TsfpgaExampleVivadoProject(VivadoProject):
    """
    Example Vivado project class.
    Shows how to override and extend the base behavior.
    """

    def pre_create(
        self,
        generics: dict[str, Any],
        **kwargs: Any,  # noqa: ANN401
    ) -> bool:
        """
        Is called right before the Vivado system call that creates the project.
        Override parent method to add custom behavior.
        """
        # Add script that elevates the severity of even more Vivado messages, to get more
        # quality feedback from the tool.
        self.tcl_sources.append(THIS_DIR / "tcl" / "example_vivado_messages.tcl")

        # Set 'build_id', which is a generic without a default value, so it is possible to
        # build the project in the GUI.
        # In a proper command-line build, it will be overridden again in 'pre_build'.
        # See 'pre_build' for more information.
        self._set_build_id_generic(generics=generics)

        return super().pre_create(generics=generics, kwargs=kwargs)

    def pre_build(
        self,
        generics: dict[str, Any],
        **kwargs: Any,  # noqa: ANN401
    ) -> bool:
        """
        Is called right before the Vivado system call that builds the project.
        Override parent method to add custom behavior.

        Note that this function is called after generating register HDL artifacts in the
        build flow.
        Hence, the register constants we set will only be available in the generated software code,
        not in the HDL.
        Hence we can run many builds in parallel, without having race conditions between the
        different values in HDL on the filesystem.
        """
        self._set_build_id_generic(generics=generics)
        self._set_build_register_constants(generics=generics)

        return super().pre_build(generics=generics, kwargs=kwargs)

    def _set_build_id_generic(self, generics: dict[str, Any]) -> None:
        """
        Set a random value.
        """
        # Set a suitable range so the generic can be handled as a VHDL 'natural'.
        # Does not need to be cryptographically secure.
        generics["build_id"] = random.randint(1, 2**25 - 1)  # noqa: S311

    def _set_build_register_constants(self, generics: dict[str, Any]) -> None:
        """
        Set register constants with build traceability information.
        """
        # Crude way of finding the module that the top-level entity belongs to.
        top_module = self.modules.get(module_name=self.top.split("_top")[0])
        registers: RegisterList = top_module.registers

        hook_note = """

Note that this constant is added by a Python build hook.
It is available in the FPGA build flow and the generated software code,
but never in the simulation flow.
"""

        registers.add_constant(
            name="expected_build_id",
            value=generics["build_id"],
            description="""\
The build ID for this FPGA build.
The value read from the **build_id** register shall be equal to this constant."""
            + hook_note,
        )

        registers.add_constant(
            name="build_project_name",
            value=self.name,
            description=(
                "The name of the build project that executed the build of this FPGA." + hook_note
            ),
        )

        registers.add_constant(
            name="build_generics",
            value=", ".join(f"{key}={value}" for key, value in generics.items()),
            description=(
                "The generic values that were set to the top level when building this FPGA."
                + hook_note
            ),
        )

        registers.add_constant(
            name="build_vivado_version",
            value=get_vivado_version(vivado_path=self._vivado_path),
            description=("The Vivado version that this FPGA was built with." + hook_note),
        )

        registers.add_constant(
            name="build_git_commit",
            value=get_git_commit(directory=REPO_ROOT),
            description="""\
The left-most characters of the git commit hash that this FPGA was built from.
If there were local changes in the git repository, this will be noted in parenthesis.
"""
            + hook_note,
        )

        registers.add_constant(
            name="build_time",
            # Specific timezone is not needed, it just needs to be consistent.
            value=(
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # noqa: DTZ005
            ),
            description="A string describing at what time and date the FPGA was built." + hook_note,
        )

        registers.add_constant(
            name="build_hostname",
            value=platform.node(),
            description="The hostname where this FPGA was built." + hook_note,
        )

        registers.add_constant(
            name="build_operating_system",
            value=platform.system(),
            description="The operating that this FPGA was built on." + hook_note,
        )

        registers.add_constant(
            name="build_operating_system_info",
            value=platform.version() + " " + platform.platform(),
            description="More information about the operating system that this FPGA was built on."
            + hook_note,
        )


class TsfpgaExampleVivadoNetlistProject(VivadoNetlistProject):
    """
    Example Vivado project class for netlist builds.
    Shows how to override and extend the base behavior.
    """

    def pre_create(
        self,
        generics: dict[str, Any],
        **kwargs: Any,  # noqa: ANN401
    ) -> bool:
        """
        Override parent method to add custom behavior.
        Update TCL sources just before project creation.
        """
        self.tcl_sources.append(THIS_DIR / "tcl" / "example_vivado_messages.tcl")
        self.tcl_sources.append(THIS_DIR / "tcl" / "example_vivado_netlist_messages.tcl")

        return super().pre_create(generics=generics, kwargs=kwargs)
