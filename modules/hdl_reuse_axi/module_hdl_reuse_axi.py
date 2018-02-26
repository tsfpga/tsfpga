from hdl_reuse.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_axi_pkg")
        tb.add_config(name="data_width_32", generics=dict(data_width=32))
        tb.add_config(name="data_width_128", generics=dict(data_width=128))
