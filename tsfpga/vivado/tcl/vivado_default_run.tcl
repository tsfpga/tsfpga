# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# A lot of information about the steps and possible settings can be found in UG904 and UG901.
#
# The names of the properties can be found by changing a setting in the GUI an see what TCL
# command is printed to the console.
# --------------------------------------------------------------------------------------------------

puts "Setting up default run"



####################################################################################################
#
# Synthesis settings
#

set_property STEPS.SYNTH_DESIGN.ARGS.DIRECTIVE Default [get_runs synth_1]

# Allows the synthesis tool to flatten the hierarchy, perform synthesis, and then rebuild the
# hierarchy based on the original RTL.
# This value allows the QoR benefit of cross-boundry optimizations with a
# final hierarchy that is similar to the RTL for ease of analysis.
set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY Rebuilt [get_runs synth_1]



####################################################################################################
#
# Implementation settings
#
# The vivado implementation flow is made up of seven steps:
# 1) Opt design
#    Optimizes the logical design to make it easier to fit onto the target device.
# 2) Pre-place power opt design (optional)
#    Optimizes design elements to reduce the power demands of the target device.
# 3) Place design
#    Places the design onto the device.
# 4) Post-place power opt design (optional)
#    Additional optimizations to reduce the power after implementation.
# 5) Post-place phys opt design (optional)
#    Optimizes logic and placement using estimated timing based on placement.
#    Includes replication of high fanout drivers.
# 6) Route design
#    Routes the design onto the device.
# 7) Post-route phys opt design
#    Optimizes logic, placement, and routing using actual routed delays.
#
# Note that steps 2 and 4 are mutually exclusive. Both can be enabled but only one will run.

# Opt design (opt_design)
set_property STEPS.OPT_DESIGN.IS_ENABLED true [get_runs impl_1]
set_property STEPS.OPT_DESIGN.ARGS.DIRECTIVE Default [get_runs impl_1]

# Pre-place power opt design (power_opt_design)
set_property STEPS.POWER_OPT_DESIGN.IS_ENABLED false [get_runs impl_1]

# Place design (place_design)
set_property STEPS.PLACE_DESIGN.ARGS.DIRECTIVE Default [get_runs impl_1]

# Post-place power opt design (power_opt_design)
set_property STEPS.POST_PLACE_POWER_OPT_DESIGN.IS_ENABLED false [get_runs impl_1]

# Post-place phys opt design (phys_opt_design)
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED false [get_runs impl_1]

# Route design (route_design)
set_property STEPS.ROUTE_DESIGN.ARGS.DIRECTIVE Default [get_runs impl_1]

# Post-route phys opt design (phys_opt_design)
set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED false [get_runs impl_1]
