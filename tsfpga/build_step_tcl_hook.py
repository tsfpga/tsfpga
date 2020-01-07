# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------


class BuildStepTclHook:

    """
    Represent a TCL file that shall be used as hook in one of the build steps.
    """

    def __init__(self, tcl_file, hook_step):
        """
        :param tcl_file: Path to a TCL file.
        :param tcl_file: Name of a build step, e.g. "STEPS.ROUTE_DESIGN.TCL.PRE".
        """
        self.tcl_file = tcl_file
        self.hook_step = hook_step

    @property
    def step_is_synth(self):
        return "synth" in self.hook_step.lower()

    def __str__(self):
        result = str(self.__class__.__name__) + ":"
        return result + f"{self.hook_step}:{self.tcl_file}"
