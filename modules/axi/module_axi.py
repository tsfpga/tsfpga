from hdl_reuse.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_axi_pkg")
        for data_width in [32, 64, 128]:
            name = "data_width_%i" % data_width
            tb.add_config(name=name, generics=dict(data_width=data_width))

        tb_axil_pkg = vunit_proj.library(self.library_name).test_bench("tb_axil_pkg")
        tb_axi_to_axil = vunit_proj.library(self.library_name).test_bench("tb_axi_to_axil")
        tb_axi_to_axil_bus_error = vunit_proj.library(self.library_name).test_bench("tb_axi_to_axil_bus_error")
        for tb in [tb_axil_pkg, tb_axi_to_axil, tb_axi_to_axil_bus_error]:
            for data_width in [32, 64]:
                name = "data_width_%i" % data_width
                tb.add_config(name=name, generics=dict(data_width=data_width))
