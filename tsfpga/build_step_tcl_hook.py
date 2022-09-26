# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


class BuildStepTclHook:

    """
    Represent a TCL file that shall be used as hook in one of the build steps.
    """

    def __init__(self, tcl_file, hook_step):
        """
        Arguments:
            tcl_file (pathlib.Path): Path to a TCL file.
            hook_step (str): Name of a build step, e.g. "STEPS.ROUTE_DESIGN.TCL.PRE".
        """
        self.tcl_file = tcl_file
        self.hook_step = hook_step

    @property
    def step_is_synth(self):
        """
        True if the build step is in synthesis. False otherwise.
        """
        return "synth" in self.hook_step.lower()

    def __str__(self):
        result = str(self.__class__.__name__) + ":"
        return result + f"{self.hook_step}:{self.tcl_file}"
