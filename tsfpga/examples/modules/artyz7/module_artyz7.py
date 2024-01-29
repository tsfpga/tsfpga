# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path

# First party libraries
from tsfpga.constraint import Constraint
from tsfpga.examples.example_env import get_hdl_modules, get_tsfpga_example_modules
from tsfpga.examples.vivado.project import TsfpgaExampleVivadoProject
from tsfpga.module import BaseModule

THIS_FILE = Path(__file__)


class Module(BaseModule):
    def get_build_projects(self):
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

        return projects
