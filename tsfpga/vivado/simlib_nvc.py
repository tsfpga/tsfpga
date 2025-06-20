# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from tsfpga.system_utils import run_command

from .simlib_open_source import VivadoSimlibOpenSource

if TYPE_CHECKING:
    from vunit.sim_if import SimulatorInterface
    from vunit.ui import VUnit


class VivadoSimlibNvc(VivadoSimlibOpenSource):
    """
    Handle Vivado simlib with NVC.

    Do not instantiate this class directly.
    Use factory class :class:`.VivadoSimlib` instead.
    """

    # NVC compilation gives a warning if the folder exist when the analyze command is executed.
    _create_library_folder_before_compile = False

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
        self.nvc_binary = Path(simulator_interface.find_prefix()) / "nvc"

        super().__init__(
            vivado_path=vivado_path,
            output_path=output_path,
            vunit_proj=vunit_proj,
            simulator_interface=simulator_interface,
        )

    def _execute_compile(
        self,
        output_path: Path,  # noqa: ARG002
        library_name: str,
        vhd_files: list[str],
    ) -> None:
        cmd = [
            str(self.nvc_binary),
            f"--work={library_name}",
            "--std=2008",
            "-M",
            "64m",
        ]
        if library_name != "unisim":
            cmd.append(
                f"--map=unisim:{self.output_path / 'unisim'}",
            )

        cmd += ["-a", *vhd_files]

        run_command(cmd, cwd=self.output_path)

    def _get_simulator_tag(self) -> str:
        """
        Return simulator version tag as a string.
        """
        cmd = [str(self.nvc_binary), "--version"]
        output = run_command(cmd, capture_output=True).stdout

        match_release = re.search(pattern=r"^nvc (\S+) \(Using.*", string=output)
        if match_release is not None:
            return self._format_version(f"nvc_{match_release.group(1)}")

        match_develop = re.search(pattern=r"^nvc (\S+) \((\S+)\) \(Using.*", string=output)
        if match_develop is not None:
            return self._format_version(f"nvc_{match_develop.group(1)}_{match_develop.group(2)}")

        raise ValueError(f"Could not find NVC version string: {output}")
