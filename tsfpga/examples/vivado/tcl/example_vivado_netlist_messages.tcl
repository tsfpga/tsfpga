# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Further file that is specific for netlist builds.
# See 'example_vivado_messages.tcl' for more details.
# --------------------------------------------------------------------------------------------------

puts "Applying example vivado netlist message rules"


# --------------------------------------------------------------------------------------------------
# Upgrade to ERROR.
# --------------------------------------------------------------------------------------------------

# Message: Generic not present in instantiated entity will be ignored.
# Motivation: This is a configuration error, we want to be notified if we set a generic that has
#     no effect.
#     This is dead code and it might make us believe that we are testing a certain thing when in
#     reality we are not.
#
# Since we apply generics before running synth_design in build_vivado_project.tcl, the generic
# value gets applied to all out-of-context IP core runs as well.
# Hence in projects where top level generics are used it is highly likely that each out-of-context
# IP core run will result in at least one of this message type.
# If this message is an ERROR, the Vivado build will fail.
# If it is a CRITICAL WARNING, the build will succeed, but Vivado will not add synthesis result to
# IP cache when this happens:
#
#    INFO: [runtcl-6] Synthesis results are not added to the cache due to CRITICAL_WARNING
#
# Hence, for these reasons, this message is upgraded to an ERROR only for netlist builds.
set_msg_config -new_severity "ERROR" -id "Synth 8-3819"
