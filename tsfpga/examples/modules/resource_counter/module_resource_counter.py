# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path

from tsfpga.examples.example_env import get_tsfpga_example_modules
from tsfpga.module import BaseModule
from tsfpga.vivado.build_result_checker import EqualTo, Ffs, LessThan, TotalLuts
from tsfpga.yosys.project import YosysXilinxNetlistBuild

THIS_FILE = Path(__file__)


class Module(BaseModule):
    def get_build_projects(self) -> list[YosysXilinxNetlistBuild]:
        """
        Netlist build(s) for the ``resource_counter`` entity, using :ref:`Yosys and the
        ghdl-yosys-plugin <yosys_netlist_build>` as an open-source, GHDL-based, alternative to a
        Vivado netlist build.

        Two variants are built, with a different ``width`` generic, to show how the resource
        utilization (in this case the flip-flop count) scales with the generic value.
        """
        # Only this module is needed, since 'resource_counter.vhd' has no dependencies on any
        # other module.
        modules = get_tsfpga_example_modules(names_include={self.name})

        return [
            YosysXilinxNetlistBuild(
                name=f"{self.library_name}.resource_counter.width_{width}",
                modules=modules,
                top="resource_counter",
                family="xc7",
                generics={"width": width},
                build_result_checkers=[
                    # One flip-flop per bit of the counter.
                    Ffs(EqualTo(width)),
                    # The combinational 'wrap_next' logic uses a small, constant, number of
                    # LUTs regardless of 'width'.
                    TotalLuts(LessThan(10)),
                ],
                defined_at=THIS_FILE,
            )
            for width in [8, 16]
        ]
