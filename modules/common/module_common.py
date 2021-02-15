# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

from tsfpga.module import BaseModule
from tsfpga.vivado.project import VivadoNetlistProject
from tsfpga.vivado.size_checker import EqualTo, Ffs, TotalLuts


class Module(BaseModule):
    def setup_vunit(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_width_conversion")

        for input_width in [8, 16, 32]:
            for output_width in [8, 16, 32]:
                if input_width == output_width:
                    continue
                test = tb.get_tests("test_data")[0]
                name = f"input_{input_width}.output_{output_width}"
                test.add_config(
                    name=name, generics=dict(input_width=input_width, output_width=output_width)
                )

        test = tb.get_tests("test_full_throughput")[0]
        test.add_config(
            name="input_16.output_8",
            generics=dict(input_width=16, output_width=8, data_jitter=False),
        )
        test.add_config(
            name="input_8.output_16",
            generics=dict(input_width=8, output_width=16, data_jitter=False),
        )

        for test in (
            vunit_proj.library(self.library_name).test_bench("tb_handshake_pipeline").get_tests()
        ):
            if "full_throughput" in test.name:
                for allow_poor_input_ready_timing in [False, True]:
                    generics = dict(
                        full_throughput=True,
                        allow_poor_input_ready_timing=allow_poor_input_ready_timing,
                    )
                    self.add_vunit_config(test=test, generics=generics)

            if "random_data" in test.name:
                for full_throughput in [False, True]:
                    for allow_poor_input_ready_timing in [False, True]:
                        generics = dict(
                            data_jitter=True,
                            full_throughput=full_throughput,
                            allow_poor_input_ready_timing=allow_poor_input_ready_timing,
                        )
                        self.add_vunit_config(test=test, generics=generics)

    def get_build_projects(self):
        projects = []
        part = "xc7z020clg400-1"
        generics = dict(data_width=32)

        generics.update(full_throughput=True, allow_poor_input_ready_timing=True)
        projects.append(
            VivadoNetlistProject(
                name=self.test_case_name("handshake_pipeline", generics),
                modules=[self],
                part=part,
                top="handshake_pipeline",
                generics=generics,
                result_size_checkers=[
                    TotalLuts(EqualTo(1)),
                    Ffs(EqualTo(34)),
                ],
            )
        )

        # Full skid-aside buffer is quite large.
        generics.update(full_throughput=True, allow_poor_input_ready_timing=False)
        projects.append(
            VivadoNetlistProject(
                name=self.test_case_name("handshake_pipeline", generics),
                modules=[self],
                part=part,
                top="handshake_pipeline",
                generics=generics,
                result_size_checkers=[
                    TotalLuts(EqualTo(37)),
                    Ffs(EqualTo(70)),
                ],
            )
        )

        generics.update(full_throughput=False, allow_poor_input_ready_timing=True)
        projects.append(
            VivadoNetlistProject(
                name=self.test_case_name("handshake_pipeline", generics),
                modules=[self],
                part=part,
                top="handshake_pipeline",
                generics=generics,
                result_size_checkers=[
                    TotalLuts(EqualTo(2)),
                    Ffs(EqualTo(34)),
                ],
            )
        )

        generics.update(full_throughput=False, allow_poor_input_ready_timing=False)
        projects.append(
            VivadoNetlistProject(
                name=self.test_case_name("handshake_pipeline", generics),
                modules=[self],
                part=part,
                top="handshake_pipeline",
                generics=generics,
                result_size_checkers=[
                    TotalLuts(EqualTo(1)),
                    Ffs(EqualTo(35)),
                ],
            )
        )

        return projects
