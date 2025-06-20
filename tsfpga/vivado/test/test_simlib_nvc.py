# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

"""
Test a subset of what is tested for GHDL, since most of the code is inherited from a
common base class.
"""

from pathlib import Path
from unittest.mock import Mock, patch

from vunit.sim_if import SimulatorInterface
from vunit.ui import VUnit

from tsfpga.vivado.simlib import VivadoSimlib


def test_version_string(tmp_path):
    def get_artifact_name(version_string: str) -> str:
        with patch("tsfpga.vivado.simlib_nvc.run_command", autospec=True) as run_command:
            run_command.return_value.stdout = version_string

            simulator_class = Mock(spec=SimulatorInterface)
            simulator_class.name = "nvc"
            simulator_class.find_prefix.return_value = "/usr/bin"

            vunit_proj = Mock(spec=VUnit)
            vunit_proj._simulator_class = simulator_class  # noqa: SLF001

            return VivadoSimlib.init(
                output_path=tmp_path,
                vunit_proj=vunit_proj,
                vivado_path=Path("/tools/xilinx/Vivado/2019.2/bin/vivado"),
            ).artifact_name

    assert ".nvc_1_17_devel_1_16_0_r71_gd381db8e." in get_artifact_name(
        version_string="nvc 1.17-devel (1.16.0.r71.gd381db8e) (Using LLVM 18.1.3)"
    )

    assert ".nvc_1_16_2." in get_artifact_name(version_string="nvc 1.16.2 (Using LLVM 18.1.3)")
