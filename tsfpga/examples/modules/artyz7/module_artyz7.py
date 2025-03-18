# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from tsfpga.constraint import Constraint
from tsfpga.examples.example_env import get_hdl_modules, get_tsfpga_example_modules
from tsfpga.examples.vivado.project import TsfpgaExampleVivadoProject
from tsfpga.module import BaseModule

if TYPE_CHECKING:
    from tsfpga.hdl_file import HdlFile

THIS_FILE = Path(__file__)


class Module(BaseModule):
    def get_build_projects(self) -> list[TsfpgaExampleVivadoProject]:
        projects = []

        modules = get_hdl_modules() + get_tsfpga_example_modules()
        part = "xc7z020clg400-1"

        tcl_dir = self.path / "tcl"
        pinning = Constraint(tcl_dir / "artyz7_pinning.tcl")
        block_design = tcl_dir / "block_design.tcl"

        projects.append(
            TsfpgaExampleVivadoProject(
                name="artyz7",
                modules=modules,
                part=part,
                tcl_sources=[block_design],
                constraints=[pinning],
                defined_at=THIS_FILE,
            )
        )

        projects.append(
            TsfpgaExampleVivadoProject(
                name="artyz7_explore",
                top="artyz7_top",
                modules=modules,
                part=part,
                tcl_sources=[block_design],
                constraints=[pinning],
                impl_explore=True,
                defined_at=THIS_FILE,
            )
        )

        projects.append(
            TsfpgaExampleVivadoProject(
                name="artyz7_verilog",
                top="artyz7_top_verilog",
                modules=modules,
                part=part,
                constraints=[pinning],
                defined_at=THIS_FILE,
            )
        )

        projects.append(
            TsfpgaExampleVivadoProject(
                name="artyz7_systemverilog",
                top="artyz7_top_systemverilog",
                modules=modules,
                part=part,
                constraints=[pinning],
                defined_at=THIS_FILE,
            )
        )

        return projects

    def get_simulation_files(
        self,
        files_avoid: bool | None = None,
        include_unisim: bool = True,
        **kwargs: Any,  # noqa: ANN401
    ) -> list[HdlFile]:
        """
        Exclude files that depend on IP cores and/or unisim.

        Note that this must be after the 'get_build_projects' method, since this file up until that
        point is included in documentation.
        """
        files_to_avoid = {
            self.path / "src" / "artyz7_top.vhd",
            self.path / "test" / "tb_artyz7_top.vhd",
        }

        if not include_unisim:
            files_avoid = files_to_avoid if files_avoid is None else files_avoid | files_to_avoid

        return super().get_simulation_files(files_avoid=files_avoid, **kwargs)
