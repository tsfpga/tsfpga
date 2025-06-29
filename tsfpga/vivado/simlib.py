# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING

from .simlib_commercial import VivadoSimlibCommercial
from .simlib_ghdl import VivadoSimlibGhdl
from .simlib_nvc import VivadoSimlibNvc

if TYPE_CHECKING:
    from pathlib import Path

    from vunit.ui import VUnit

    from .simlib_common import VivadoSimlibCommon


class VivadoSimlib:
    """
    Factory class for getting a Vivado simlib API.
    """

    @staticmethod
    def init(
        output_path: Path, vunit_proj: VUnit, vivado_path: Path | None = None
    ) -> VivadoSimlibCommon:
        """
        Get a Vivado simlib API suitable for your current simulator.
        Uses VUnit mechanism for detecting the simulator currently in use.

        Will return a :class:`.VivadoSimlibCommon` subclass object.

        Arguments:
            output_path: The compiled simlib will be placed here.
            vunit_proj: The VUnit project that is used to run simulation.
            vivado_path: Path to Vivado executable.
                If left out, the default from system ``PATH`` will be used.
        """
        simulator_interface = vunit_proj._simulator_class  # noqa: SLF001

        if simulator_interface is None:
            raise RuntimeError("VUnit found no simulator. Can not proceed.")

        if simulator_interface.name == "ghdl":
            return VivadoSimlibGhdl(
                vivado_path=vivado_path,
                output_path=output_path,
                vunit_proj=vunit_proj,
                simulator_interface=simulator_interface,
            )

        if simulator_interface.name == "nvc":
            return VivadoSimlibNvc(
                vivado_path=vivado_path,
                output_path=output_path,
                vunit_proj=vunit_proj,
                simulator_interface=simulator_interface,
            )

        return VivadoSimlibCommercial(
            vivado_path=vivado_path,
            output_path=output_path,
            vunit_proj=vunit_proj,
            simulator_interface=simulator_interface,
        )
