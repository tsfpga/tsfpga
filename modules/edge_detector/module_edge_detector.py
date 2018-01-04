from hdl_reuse.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb_edge_detector = vunit_proj.library(self.library_name).entity("tb_edge_detector")
        tb_edge_detector.add_config(name="2", generics=dict(wait_time_ms=2))
        tb_edge_detector.add_config(name="3", generics=dict(wait_time_ms=3))
