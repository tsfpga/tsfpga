# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_afifo")
        for width in [8, 24]:
            for depth in [16, 1024]:
                name = f"width_{width}.depth_{depth}"
                tb.add_config(name=name, generics=dict(width=width, depth=depth))

        # Note that
        #   almost full level to depth
        #   empty level of 1
        # will exclude level counter
        for test in vunit_proj.library(self.library_name).test_bench("tb_fifo").get_tests():
            if "almost" in test.name:
                width = 24
                depth = 1024
                for almost_full_level in [depth, depth // 2]:
                    for almost_empty_level in [1, depth // 4]:
                        name = f"almost_full_level_{almost_full_level}.almost_empty_level_{almost_empty_level}"
                        generics = dict(width=width,
                                        depth=depth,
                                        almost_full_level=almost_full_level,
                                        almost_empty_level=almost_empty_level)
                        test.add_config(name=name, generics=generics)
            else:
                for width in [8, 24]:
                    for depth in [16, 1024]:
                        name = f"width_{width}.depth_{depth}.no_level_counter"
                        generics = dict(width=width,
                                        depth=depth,
                                        almost_full_level=depth,
                                        almost_empty_level=1)
                        test.add_config(name=name, generics=generics)

                name = f"include_level_counter"
                generics = dict(width=8,
                                depth=256,
                                almost_full_level=73,
                                almost_empty_level=31)
                test.add_config(name=name, generics=generics)
