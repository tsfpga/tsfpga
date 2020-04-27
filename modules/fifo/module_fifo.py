# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):  # pylint: disable=too-many-branches
        # Note that
        #   almost_full_level = depth, or
        #   almost_empty_level = 0
        # result in alternative ways of calculating almost full/empty.

        for read_clock_is_faster in [True, False]:
            name = "read_clock_faster" if read_clock_is_faster else "write_clock_faster"
            for test in vunit_proj.library(self.library_name).test_bench("tb_afifo").get_tests():
                if "almost" in test.name or "init_state" in test.name:
                    depth = 1024
                    for almost_full_level in [depth, depth // 2]:
                        for almost_empty_level in [0, depth // 4]:
                            test_case_name = f"{name}.almost_full_level_{almost_full_level}.almost_empty_level_{almost_empty_level}"
                            generics = dict(depth=depth,
                                            almost_full_level=almost_full_level,
                                            almost_empty_level=almost_empty_level,
                                            read_clock_is_faster=read_clock_is_faster)
                            test.add_config(name=test_case_name, generics=generics)
                else:
                    for depth in [16, 1024]:
                        test_case_name = f"{name}.depth_{depth}"
                        generics = dict(depth=depth,
                                        almost_full_level=0,
                                        almost_empty_level=depth,
                                        read_clock_is_faster=read_clock_is_faster)
                        test.add_config(name=test_case_name, generics=generics)

        for test in vunit_proj.library(self.library_name).test_bench("tb_fifo").get_tests():
            if "almost" in test.name:
                depth = 1024
                for almost_full_level in [depth, depth // 2]:
                    for almost_empty_level in [0, depth // 4]:
                        name = f"almost_full_level_{almost_full_level}.almost_empty_level_{almost_empty_level}"
                        generics = dict(depth=depth,
                                        almost_full_level=almost_full_level,
                                        almost_empty_level=almost_empty_level)
                        test.add_config(name=name, generics=generics)
            else:
                for depth in [16, 1024]:
                    name = f"depth_{depth}"
                    generics = dict(depth=depth,
                                    almost_full_level=depth,
                                    almost_empty_level=0,
                                    enable_last=True)

                    if "write_faster_than_read" in test.name:
                        generics.update(read_stall_probability_percent=75)
                    if "read_faster_than_write" in test.name:
                        generics.update(write_stall_probability_percent=75)
                    if "packet_mode" in test.name:
                        generics.update(enable_packet_mode=True)

                    test.add_config(name=name, generics=generics)
