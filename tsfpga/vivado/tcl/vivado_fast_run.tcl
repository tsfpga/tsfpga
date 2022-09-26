# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------


puts "Setting up fast run"


####################################################################################################
#
# Synthesis settings
#
create_run synth_2 -flow [get_property FLOW [get_runs synth_1]]
set_property STRATEGY Flow_RuntimeOptimized [get_runs synth_2]



####################################################################################################
#
# Implementation settings
#
create_run impl_2 -parent_run synth_2 -flow [get_property FLOW [get_runs impl_1]]
set_property STRATEGY Flow_RuntimeOptimized [get_runs impl_2]

# This option shortens router runtime at the expense of repeatability. With -ultrathreads,
# the router runs faster but there is a variation in routing between identical runs.
set_property -name {STEPS.PHYS_OPT_DESIGN.ARGS.MORE OPTIONS} -value -ultrathreads \
  -objects [get_runs impl_2]
