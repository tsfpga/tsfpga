# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

import hashlib
from pathlib import Path

from tsfpga.system_utils import create_file
from .common import get_vivado_path, run_vivado_tcl, to_tcl_path
from .simlib_common import VivadoSimlibCommon


class VivadoSimlibCommercial(VivadoSimlibCommon):

    """
    Handle Vivado simlib with a commercial simulator.
    """

    _libraries = ["unisim", "secureip", "unimacro", "unifast", "xpm"]

    _tcl = (
        "set_param general.maxthreads 4\n"
        "compile_simlib -simulator {simulator_name} -simulator_exec_path {{{simulator_folder}}} "
        "-family all -language all -library all -no_ip_compile -dir {{{output_path}}} -force"
    )

    def __init__(self, output_path, vunit_proj, simulator_interface, vivado_path):
        """
        Arguments:
            output_path (`pathlib.Path`): The compiled simlib will be placed here.
            vunit_proj: The VUnit project that is used to run simulation.
            simulator_interface: A VUnit SimulatorInterface class.
            vivado_path (`pathlib.Path`): Path to Vivado executable.
        """
        self._vunit_proj = vunit_proj
        self._vivado_path = get_vivado_path(vivado_path)

        # Vivado uses a different name for Riviera-PRO
        self._simulator_name = (
            "riviera" if simulator_interface.name == "rivierapro" else simulator_interface.name
        )
        self._simulator_folder = Path(simulator_interface.find_prefix())

        self._output_path = output_path / self._get_version_tag()

    def _compile(self):
        tcl_file = self._output_path / "compile_simlib.tcl"
        tcl = self._tcl.format(
            simulator_name=self._simulator_name,
            simulator_folder=to_tcl_path(self._simulator_folder),
            output_path=to_tcl_path(self._output_path),
        )
        create_file(tcl_file, tcl)
        run_vivado_tcl(self._vivado_path, tcl_file)

    def _get_version_tag(self):
        """
        Add a hash of the TCL script to version tag.
        """
        tag = super()._get_version_tag()
        tag += "." + self._get_tcl_hash()
        return tag

    def _get_simulator_tag(self):
        """
        Return e.g. modelsim_modeltech_pe_10_6c or riviera_riviera_pro_2018_10_x64.
        """
        simulator_version = self._simulator_folder.parent.name
        return self._format_version(f"{self._simulator_name}_{simulator_version}")

    def _get_tcl_hash(self):
        """
        Return a (partial) hash of the TCL script that is used to compile simlib.
        """
        return hashlib.md5(self._tcl.encode()).hexdigest()[0:8]

    def _add_to_vunit_project(self):
        """
        Add the compiled simlib to your VUnit project.
        """
        for library in self._libraries:
            library_path = self._output_path / library
            assert library_path.exists(), library_path
            self._vunit_proj.add_external_library(library, library_path)
