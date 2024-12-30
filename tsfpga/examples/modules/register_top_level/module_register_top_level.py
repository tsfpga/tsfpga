# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# Standard libraries
from pathlib import Path
from typing import TYPE_CHECKING

# Third party libraries
from hdl_registers.parser.toml import from_toml

# First party libraries
from tsfpga.examples.example_env import get_hdl_modules, get_tsfpga_example_modules
from tsfpga.examples.vivado.project import TsfpgaExampleVivadoProject
from tsfpga.module import BaseModule

if TYPE_CHECKING:
    # Third party libraries
    from hdl_registers.register_list import RegisterList

THIS_FILE = Path(__file__)


class Module(BaseModule):
    def get_build_projects(self):
        projects = []

        modules = get_hdl_modules() + get_tsfpga_example_modules()
        part = "xc7z020clg400-1"

        block_design = (
            modules.get(module_name="artyz7_block_design").path / "tcl" / "block_design.tcl"
        )

        projects.append(
            TsfpgaExampleVivadoProject(
                name="axi_lite_register_top_level",
                modules=modules,
                part=part,
                tcl_sources=[block_design],
                defined_at=THIS_FILE,
            )
        )

        return projects

    @property
    def registers(self) -> "RegisterList":
        """
        Get the registers for this module.
        Overload the method to avoid inserting default registers.
        To make the resource utilization as predictable and fair as possible.
        """
        return from_toml(name=self.name, toml_file=self.register_data_file)
