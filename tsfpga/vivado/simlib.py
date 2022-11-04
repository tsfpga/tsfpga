# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Local folder libraries
from .simlib_commercial import VivadoSimlibCommercial
from .simlib_ghdl import VivadoSimlibGhdl


class VivadoSimlib:

    """
    Factory class for getting a Vivado simlib API.
    """

    @staticmethod
    def init(output_path, vunit_proj, vivado_path=None):
        """
        Get a Vivado simlib API suitable for your current simulator. Uses VUnit mechanism
        for detecting the simulator currently in use.

        Arguments:
            output_path (pathlib.Path): The compiled simlib will be placed here.
            vunit_proj: The VUnit project that is used to run simulation.
            vivado_path (pathlib.Path): Path to Vivado executable. If left out, the default
                from system ``PATH`` will be used.
        Return:
            A :class:`.VivadoSimlibCommon` child object.
        """
        simulator_interface = vunit_proj._simulator_class  # pylint: disable=protected-access
        if simulator_interface.name == "ghdl":
            return VivadoSimlibGhdl(output_path, vunit_proj, simulator_interface, vivado_path)
        return VivadoSimlibCommercial(output_path, vunit_proj, simulator_interface, vivado_path)
