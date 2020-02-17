# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_axil_reg_file")
        tb.test("read_from_non_existent_register").set_generic("use_axil_bfm", False)
        tb.test("read_from_non_read_type_register").set_generic("use_axil_bfm", False)
        tb.test("write_to_non_existent_register").set_generic("use_axil_bfm", False)
        tb.test("write_to_non_write_type_register").set_generic("use_axil_bfm", False)
