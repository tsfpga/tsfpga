# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path


class BuildStepTclHook:
    """
    Represent a TCL file that shall be used as hook in one of the build steps.
    """

    def __init__(self, tcl_file: Path, hook_step: str) -> None:
        """
        Arguments:
            tcl_file: Path to a TCL file.
            hook_step: Name of a build step, e.g. ``STEPS.ROUTE_DESIGN.TCL.PRE``.
               See
               https://docs.xilinx.com/r/en-US/ug894-vivado-tcl-scripting/Defining-Tcl-Hook-Scripts
               for a list of the available build steps in AMD Vivado.
        """
        self.tcl_file = tcl_file
        self.hook_step = hook_step

    @property
    def step_is_synth(self) -> bool:
        """
        True if the build step is in synthesis. False otherwise.
        """
        return "synth" in self.hook_step.lower()

    def __str__(self) -> str:
        result = str(self.__class__.__name__) + ":"
        return result + f"{self.hook_step}:{self.tcl_file}"
