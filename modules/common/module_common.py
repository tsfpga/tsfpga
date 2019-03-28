# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_width_conversion")

        for input_width in [8, 16, 32]:
            for output_width in [8, 16, 32]:
                if input_width == output_width:
                    continue
                test = tb.get_tests("test_data")[0]
                name = "input_%i.output_%s" % (input_width, output_width)
                test.add_config(name=name, generics=dict(input_width=input_width, output_width=output_width))

        test = tb.get_tests("test_full_throughput")[0]
        test.add_config(name="input_16.output_8", generics=dict(input_width=16, output_width=8, data_jitter=False))
        test.add_config(name="input_8.output_16", generics=dict(input_width=8, output_width=16, data_jitter=False))

        test = vunit_proj.library(self.library_name).test_bench("tb_handshake_pipeline").get_tests("test_full_throughput")[0]
        test.set_generic("data_jitter", False)
