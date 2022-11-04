# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path

# First party libraries
from tsfpga.build_step_tcl_hook import BuildStepTclHook


def test_step_is_synth():
    assert BuildStepTclHook(Path(), "STEPS.SYNTH_DESIGN.TCL.PRE").step_is_synth
    assert not BuildStepTclHook(Path(), "STEPS.ROUTE_DESIGN.TCL.PRE").step_is_synth


def test_can_cast_to_string_without_error():
    str(BuildStepTclHook(Path("some_file.tcl"), "STEPS.SYNTH_DESIGN.TCL.PRE"))
