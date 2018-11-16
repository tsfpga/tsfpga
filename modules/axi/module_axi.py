from hdl_reuse.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_axi_pkg")
        for data_width in [32, 64, 128]:
            for id_width in [0, 32]:
                name = "data_width_%i.id_width_%s" % (data_width, id_width)
                tb.add_config(name=name, generics=dict(data_width=data_width, id_width=id_width))

        for tb_name in ["tb_axil_pkg", "tb_axi_to_axil", "tb_axi_to_axil_bus_error"]:
            tb = vunit_proj.library(self.library_name).test_bench(tb_name)
            for data_width in [32, 64]:
                name = "data_width_%i" % data_width
                tb.add_config(name=name, generics=dict(data_width=data_width))

        tb = vunit_proj.library(self.library_name).test_bench("tb_axil_cdc")
        tb.add_config(name="input_clk_fast", generics=dict(input_clk_fast=True))
        tb.add_config(name="output_clk_fast", generics=dict(output_clk_fast=True))
        tb.add_config(name="same_clocks")
