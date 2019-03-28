# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        for tb_name in ["tb_fifo", "tb_afifo"]:
            tb = vunit_proj.library(self.library_name).test_bench(tb_name)
            for width in [8, 24]:
                for depth in [16, 1024]:
                    name = "width_%i.depth_%i" % (width, depth)
                    tb.add_config(name=name, generics=dict(width=width, depth=depth))
