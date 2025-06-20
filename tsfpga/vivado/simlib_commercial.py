# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from tsfpga.system_utils import create_file

from .common import run_vivado_tcl, to_tcl_path
from .simlib_common import VivadoSimlibCommon

if TYPE_CHECKING:
    from vunit.sim_if import SimulatorInterface
    from vunit.ui import VUnit


class VivadoSimlibCommercial(VivadoSimlibCommon):
    """
    Handle Vivado simlib with a commercial simulator.

    Do not instantiate this class directly.
    Use factory class :class:`.VivadoSimlib` instead.
    """

    library_names: ClassVar = ["unisim", "secureip", "unimacro", "unifast", "xpm"]

    _tcl = (
        "set_param general.maxthreads 8\n"
        "compile_simlib "
        "-simulator {simulator_name} "
        "-simulator_exec_path {{{simulator_folder}}} "
        "-directory {{{output_path}}} "
        "-force "
        "-family all "
        "-language all "
        "-library all "
        "-no_ip_compile "
        "-no_systemc_compile "
    )

    def __init__(
        self,
        vivado_path: Path | None,
        output_path: Path,
        vunit_proj: VUnit,
        simulator_interface: SimulatorInterface,
    ) -> None:
        """
        See superclass :class:`.VivadoSimlibCommon` constructor for details.
        """
        self._simulator_folder = Path(simulator_interface.find_prefix())
        self._simulator_name = self._get_simulator_name(simulator_interface=simulator_interface)

        super().__init__(
            vivado_path=vivado_path,
            output_path=output_path,
            vunit_proj=vunit_proj,
            simulator_interface=simulator_interface,
        )

    def _get_simulator_name(self, simulator_interface: SimulatorInterface) -> str:
        """
        Used to get the "-simulator" argument to the Vivado "compile_simlib" function.
        In some cases Vivado needs a different simulator name than what is used in VUnit.

        Arguments:
            simulator_interface: A VUnit SimulatorInterface object.

        Return:
            str: The simulator name preferred by Vivado.
        """
        # Aldec Riviera-PRO is called "rivierapro" in VUnit but Vivado needs the name "riviera"
        if simulator_interface.name == "rivierapro":
            return "riviera"

        # Siemens Questa is called "modelsim" in VUnit but Vivado needs the name "questasim".
        # See discussion in
        #   https://github.com/VUnit/vunit/issues/834
        # Use the simulator installation path to decode whether we are running Questa or
        # regular ModelSim.
        if "questa" in str(self._simulator_folder).lower():
            return "questasim"

        # In other cases Vivado uses the same name as VUnit.
        # We do not do typing of the 'simulator_interface', but we know that '.name' is a string.
        return simulator_interface.name

    def _compile(self) -> None:
        tcl_file = self.output_path / "compile_simlib.tcl"
        tcl = self._tcl.format(
            simulator_name=self._simulator_name,
            simulator_folder=to_tcl_path(self._simulator_folder),
            output_path=to_tcl_path(self.output_path),
        )
        create_file(tcl_file, tcl)
        compile_ok = run_vivado_tcl(self._vivado_path, tcl_file)

        if not compile_ok:
            raise RuntimeError("Vivado simlib compile call failed!")

    def _get_simulator_tag(self) -> str:
        """
        Return e.g. modelsim_modeltech_pe_10_6c or riviera_riviera_pro_2018_10_x64.
        """
        simulator_version = self._simulator_folder.parent.name
        return self._format_version(f"{self._simulator_name}_{simulator_version}")
