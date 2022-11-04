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
from tsfpga.system_utils import create_file

# Local folder libraries
from .common import get_vivado_path, run_vivado_tcl, to_tcl_path
from .simlib_common import VivadoSimlibCommon


class VivadoSimlibCommercial(VivadoSimlibCommon):

    """
    Handle Vivado simlib with a commercial simulator.
    """

    library_names = ["unisim", "secureip", "unimacro", "unifast", "xpm"]

    _tcl = (
        "set_param general.maxthreads 4\n"
        "compile_simlib -simulator {simulator_name} -simulator_exec_path {{{simulator_folder}}} "
        "-family all -language all -library all -no_ip_compile -dir {{{output_path}}} -force"
    )

    def __init__(self, output_path, vunit_proj, simulator_interface, vivado_path):
        """
        Arguments:
            output_path (pathlib.Path): The compiled simlib will be placed here.
            vunit_proj: The VUnit project that is used to run simulation.
            simulator_interface: A VUnit SimulatorInterface object.
            vivado_path (pathlib.Path): Path to Vivado executable.
        """
        self._vunit_proj = vunit_proj
        self._vivado_path = get_vivado_path(vivado_path)

        self._simulator_folder = Path(simulator_interface.find_prefix())
        self._simulator_name = self._get_simulator_name(simulator_interface=simulator_interface)

        self.output_path = output_path / self._get_version_tag()

    def _get_simulator_name(self, simulator_interface):
        """
        Used to get the "-simulator" argument to the Vivado "compile_simlib" function.
        In some cases Vivado needs a different simulator name than what is used in VUnit.

        Arguments:
            simulator_interface: A VUnit SimulatorInterface object.

        Returns:
            str: The simulator name preferred by Vivado.
        """
        # Aldec Riviera-PRO is called "rivierapro" in VUnit but Vivado needs the name "riviera"
        if simulator_interface.name == "rivierapro":
            return "riviera"

        # Siemens Questa is called "modelsim" in VUnit but Vivado needs the name "questasim".
        # See discussion in
        #   https://github.com/VUnit/vunit/issues/834
        #   https://gitlab.com/tsfpga/tsfpga/-/issues/67
        # Use the simulator installation path to decode whether we are running Questa or
        # regular ModelSim.
        if "questa" in str(self._simulator_folder).lower():
            return "questasim"

        # In other cases Vivado uses the same name as VUnit
        return simulator_interface.name

    def _compile(self):
        tcl_file = self.output_path / "compile_simlib.tcl"
        tcl = self._tcl.format(
            simulator_name=self._simulator_name,
            simulator_folder=to_tcl_path(self._simulator_folder),
            output_path=to_tcl_path(self.output_path),
        )
        create_file(tcl_file, tcl)
        run_vivado_tcl(self._vivado_path, tcl_file)

    def _get_simulator_tag(self):
        """
        Return e.g. modelsim_modeltech_pe_10_6c or riviera_riviera_pro_2018_10_x64.
        """
        simulator_version = self._simulator_folder.parent.name
        return self._format_version(f"{self._simulator_name}_{simulator_version}")

    def _add_to_vunit_project(self):
        """
        Add the compiled simlib to your VUnit project.
        """
        for library_name in self.library_names:
            library_path = self.output_path / library_name
            assert library_path.exists(), library_path
            self._vunit_proj.add_external_library(library_name, library_path)
