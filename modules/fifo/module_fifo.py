# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        for test in vunit_proj.library(self.library_name).test_bench("tb_afifo").get_tests():
            for read_clock_is_faster in [True, False]:
                original_generics = dict(read_clock_is_faster=read_clock_is_faster)

                for generics in self.generate_common_fifo_test_generics(test.name, original_generics):
                    self.add_config(test, generics)

        for test in vunit_proj.library(self.library_name).test_bench("tb_fifo").get_tests():
            for generics in self.generate_common_fifo_test_generics(test.name):
                self.add_config(test, generics)

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

    def add_config(self, test, generics):
        test.add_config(self.generics_to_string(generics), generics)
