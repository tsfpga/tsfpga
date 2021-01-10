# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule
from tsfpga.vivado.project import VivadoNetlistProject
from tsfpga.vivado.size_checker import EqualTo, Ffs, LogicLuts, Ramb18, Ramb36, TotalLuts
from examples.tsfpga_example_env import get_tsfpga_modules


class Module(BaseModule):
    def setup_vunit(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_axil_reg_file")
        tb.test("read_from_non_existent_register").set_generic("use_axil_bfm", False)
        tb.test("read_from_non_read_type_register").set_generic("use_axil_bfm", False)
        tb.test("write_to_non_existent_register").set_generic("use_axil_bfm", False)
        tb.test("write_to_non_write_type_register").set_generic("use_axil_bfm", False)

    def setup_formal(self, formal_proj, **kwargs):
        formal_proj.add_config(
            top="axil_reg_file_wrapper",
            engine_command="smtbmc",
            solver_command="z3",
            mode="prove",
        )

    def get_build_projects(self):  # pylint: disable=no-self-use
        projects = []
        all_modules = get_tsfpga_modules()
        part = "xc7z020clg400-1"

        projects.append(
            VivadoNetlistProject(
                name="axil_reg_file",
                modules=all_modules,
                part=part,
                top="axil_reg_file_wrapper",
                result_size_checkers=[
                    TotalLuts(EqualTo(199)),
                    LogicLuts(EqualTo(199)),
                    Ffs(EqualTo(456)),
                    Ramb36(EqualTo(0)),
                    Ramb18(EqualTo(0)),
                ],
            )
        )

        return projects
