# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

from tsfpga.module import BaseModule


class Module(BaseModule):

    def setup_simulations(self, vunit_proj, **kwargs):
        tb = vunit_proj.library(self.library_name).test_bench("tb_resync_pulse")
        for input_pulse_overload in [True, False]:
            name = "pulse_gating." if input_pulse_overload else ""

            generics = dict(input_pulse_overload=input_pulse_overload, output_clock_is_faster=True)
            tb.add_config(name=name + "output_clock_is_faster", generics=generics)

            generics = dict(input_pulse_overload=input_pulse_overload)
            tb.add_config(name=name + "output_clock_is_same", generics=generics)

            generics = dict(input_pulse_overload=input_pulse_overload, output_clock_is_slower=True)
            tb.add_config(name=name + "output_clock_is_slower", generics=generics)

        tb = vunit_proj.library(self.library_name).test_bench("tb_resync_counter")
        for pipeline_output in [True, False]:
            name = "pipeline_output" if pipeline_output else "dont_pipeline_output"

            generics = dict(pipeline_output=pipeline_output)
            tb.add_config(name=name, generics=generics)
