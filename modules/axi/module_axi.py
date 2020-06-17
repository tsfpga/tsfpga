# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_axi_pkg")
        for data_width in [32, 64]:
            for id_width in [0, 5]:
                for addr_width in [32, 40]:
                    generics = dict(data_width=data_width, id_width=id_width, addr_width=addr_width)
                    name = self.generics_to_string(generics)
                    tb.add_config(name=name, generics=generics)

        tb = vunit_proj.library(self.library_name).test_bench("tb_axil_pkg")
        for data_width in [32, 64]:
            for addr_width in [32, 40]:
                generics = dict(data_width=data_width, addr_width=addr_width)
                name = self.generics_to_string(generics)
                tb.add_config(name=name, generics=generics)

        for tb_name in ["tb_axi_to_axil", "tb_axi_to_axil_bus_error"]:
            tb = vunit_proj.library(self.library_name).test_bench(tb_name)
            for data_width in [32, 64]:
                name = "data_width_%i" % data_width
                tb.add_config(name=name, generics=dict(data_width=data_width))

        tb = vunit_proj.library(self.library_name).test_bench("tb_axil_cdc")
        tb.add_config(name="master_clk_fast", generics=dict(master_clk_fast=True))
        tb.add_config(name="slave_clk_fast", generics=dict(slave_clk_fast=True))
        tb.add_config(name="same_clocks")

        tb = vunit_proj.library(self.library_name).test_bench("tb_axi_fifo")
        tb.add_config(name="passthrough", generics=dict(depth=0))
        tb.add_config(name="synchronous", generics=dict(depth=16, asynchronous=False))
        tb.add_config(name="asynchronous", generics=dict(depth=16, asynchronous=True))

        tb = vunit_proj.library(self.library_name).test_bench("tb_axi_interconnect")
        tb.add_config(name="axi_lite", generics=dict(test_axi_lite=True))
        tb.add_config(name="axi", generics=dict(test_axi_lite=False))

        tb = vunit_proj.library(self.library_name).test_bench("tb_axil_mux")
        tb.test("read_from_non_existent_slave_base_adress").set_generic("use_axil_bfm", False)
        tb.test("write_to_non_existent_slave_base_adress").set_generic("use_axil_bfm", False)
