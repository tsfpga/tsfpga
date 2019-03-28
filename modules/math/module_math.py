# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_unsigned_divider")
        for dividend_width in [4, 7, 8]:
            for divisor_width in [4, 7, 8]:
                name = "%i_div_%i" % (dividend_width, divisor_width)
                tb.add_config(name=name, generics=dict(dividend_width=dividend_width, divisor_width=divisor_width))
