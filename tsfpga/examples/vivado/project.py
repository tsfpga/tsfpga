# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path
from typing import Any

# First party libraries
from tsfpga.vivado.project import VivadoNetlistProject, VivadoProject

THIS_DIR = Path(__file__).parent


class TsfpgaExampleVivadoProject(VivadoProject):
    """
    Example Vivado project class.
    Shows how to override and extend the base behavior.
    """

    def pre_create(  # type: ignore[override]  # pylint: disable=arguments-differ
        self, generics: dict[str, Any], **kwargs: Any
    ) -> bool:
        """
        Override parent method to add custom behavior.
        Update TCL sources just before project creation.
        """
        self.tcl_sources.append(THIS_DIR / "tcl" / "example_vivado_messages.tcl")
        self.tcl_sources.append(THIS_DIR / "tcl" / "example_vivado_message_undriven_pin.tcl")

        return super().pre_create(generics=generics, kwargs=kwargs)


class TsfpgaExampleVivadoNetlistProject(VivadoNetlistProject):
    """
    Example Vivado project class for netlist builds.
    Shows how to override and extend the base behavior.
    """

    def pre_create(  # type: ignore[override]  # pylint: disable=arguments-differ
        self, generics: dict[str, Any], **kwargs: Any
    ) -> bool:
        """
        Override parent method to add custom behavior.
        Update TCL sources just before project creation.
        """
        self.tcl_sources.append(THIS_DIR / "tcl" / "example_vivado_messages.tcl")
        self.tcl_sources.append(THIS_DIR / "tcl" / "example_vivado_message_undriven_pin.tcl")
        self.tcl_sources.append(THIS_DIR / "tcl" / "example_vivado_netlist_messages.tcl")

        return super().pre_create(generics=generics, kwargs=kwargs)
