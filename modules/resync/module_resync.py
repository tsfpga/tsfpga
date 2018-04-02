from hdl_reuse.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_pulse_resync")
        for input_pulse_overload in [True, False]:
            name = "pulse_gating." if input_pulse_overload else ""

            generics = dict(input_pulse_overload=input_pulse_overload, output_clock_is_faster=True)
            tb.add_config(name=name + "output_clock_is_faster", generics=generics)

            generics = dict(input_pulse_overload=input_pulse_overload)
            tb.add_config(name=name + "output_clock_is_same", generics=generics)

            generics = dict(input_pulse_overload=input_pulse_overload, output_clock_is_slower=True)
            tb.add_config(name=name + "output_clock_is_slower", generics=generics)
