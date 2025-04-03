# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from tsfpga.constraint import Constraint
from tsfpga.examples.example_env import get_hdl_modules, get_tsfpga_example_modules
from tsfpga.examples.vivado.project import TsfpgaExampleVivadoProject
from tsfpga.module import BaseModule

if TYPE_CHECKING:
    from vunit.ui import VUnit

THIS_FILE = Path(__file__)


class Module(BaseModule):
    def get_build_projects(self) -> list[TsfpgaExampleVivadoProject]:
        modules = get_hdl_modules() + get_tsfpga_example_modules()
        part = "xc7z020clg400-1"

        constraints = [
            Constraint(self.path / "tcl" / "input_source_synchronous.tcl", used_in_synthesis=False),
            Constraint(self.path / "tcl" / "input_system_synchronous.tcl", used_in_synthesis=False),
            Constraint(self.path / "tcl" / "input_sink_synchronous.tcl", used_in_synthesis=False),
        ]
        block_design = modules.get("artyz7").path / "tcl" / "block_design.tcl"

        return [
            TsfpgaExampleVivadoProject(
                name="io_constraints",
                modules=modules,
                part=part,
                tcl_sources=[block_design],
                constraints=constraints,
                defined_at=THIS_FILE,
            )
        ]

    def setup_vunit(
        self,
        vunit_proj: VUnit,
        include_unisim: bool = True,
        **kwargs,  # noqa: ANN003, ARG002
    ) -> None:
        vunit_proj.library(self.library_name).test_bench("tb_io_constraints_top").set_generic(
            name="mock_unisim", value=not include_unisim
        )
