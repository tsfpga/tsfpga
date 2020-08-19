# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule
from tsfpga.vivado.project import VivadoNetlistProject
from tsfpga.vivado.size_checker import *  # pylint: disable=wildcard-import,unused-wildcard-import
from examples.tsfpga_example_env import get_tsfpga_modules


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        for test in vunit_proj.library(self.library_name).test_bench("tb_afifo").get_tests():
            for read_clock_is_faster in [True, False]:
                original_generics = dict(read_clock_is_faster=read_clock_is_faster)

                for generics in self.generate_common_fifo_test_generics(test.name, original_generics):
                    self.add_config(test, generics=generics)

        for test in vunit_proj.library(self.library_name).test_bench("tb_fifo").get_tests():
            for generics in self.generate_common_fifo_test_generics(test.name):
                self.add_config(test, generics=generics)

    @staticmethod
    def generate_common_fifo_test_generics(test_name, original_generics=None):
        generics = original_generics if original_generics is not None else dict()

        if "init_state" in test_name or "almost" in test_name:
            # Note that
            #   almost_full_level = depth, or
            #   almost_empty_level = 0
            # result in alternative ways of calculating almost full/empty.
            depth = 32

            for almost_full_level, almost_empty_level in [(depth, depth // 2), (depth // 2, 0)]:
                generics.update(depth=depth,
                                almost_full_level=almost_full_level,
                                almost_empty_level=almost_empty_level)

                yield generics

        else:
            if "write_faster_than_read" in test_name:
                generics.update(read_stall_probability_percent=90)
                generics.update(enable_last=True)
            if "read_faster_than_write" in test_name:
                generics.update(write_stall_probability_percent=90)
            if "packet_mode" in test_name:
                generics.update(enable_packet_mode=True, enable_last=True)

            for depth in [16, 512]:
                generics.update(depth=depth)

                yield generics

    def setup_formal(self, formal_proj, **kwargs):
        depth = 4
        for (almost_full_level, almost_empty_level) in [(depth - 1, 0), (depth, 1)]:
            generics = dict(
                width=3,
                depth=depth,
                almost_full_level=almost_full_level,
                almost_empty_level=almost_empty_level)
            formal_proj.add_config(top="fifo", generics=generics)

    def get_build_projects(self):
        projects = []
        all_modules = get_tsfpga_modules()
        part = "xc7z020clg400-1"

        # Use a wrapper as top level, which only routes the "barebone" ports, resulting in
        # a minimal FIFO.
        generics = dict(width=32, depth=1024)
        projects.append(VivadoNetlistProject(
            name=self.test_case_name("fifo_minimal", generics),
            modules=all_modules,
            part=part,
            top="fifo_netlist_build_wrapper",
            generics=generics,
            result_size_checkers=[
                TotalLuts(EqualTo(16)),
                LogicLuts(EqualTo(16)),
                Ffs(EqualTo(24)),
                Ramb36(EqualTo(1)),
                Ramb18(EqualTo(0)),
            ]
        ))

        # A FIFO with level counter port and non-default almost_full_level, which
        # increases resource utilization.
        generics = dict(width=32, depth=1024, almost_full_level=800)
        projects.append(VivadoNetlistProject(
            name=self.test_case_name("fifo_regular", generics),
            modules=all_modules,
            part=part,
            top="fifo",
            generics=generics,
            result_size_checkers=[
                TotalLuts(EqualTo(29)),
                LogicLuts(EqualTo(29)),
                Ffs(EqualTo(35)),
                Ramb36(EqualTo(1)),
                Ramb18(EqualTo(0)),
            ]
        ))

        return projects
