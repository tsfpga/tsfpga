# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from tsfpga.build_result import BuildResult


class YosysBuildResult(BuildResult):
    """
    The result of a Yosys netlist build.

    Yosys builds are synthesis-only, so there are no implementation metrics and no timing
    information. Only :attr:`.BuildResult.synthesis_size` is available.
    """
