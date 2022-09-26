# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Set the severity of various Vivado mesages
#
# A lot of WARNINGs from Vivado are not interesting. They should be suppressed as to not clutter
# the logs. This is achieved by lowering their severity to INFO.
#
# For some inspiration see https://github.com/slaclab/ruckus/blob/main/vivado/messages.tcl
# --------------------------------------------------------------------------------------------------

puts "Applying vivado messages"


# --------------------------------------------------------------------------------------------------
# Downgrade
# --------------------------------------------------------------------------------------------------

# Message:
#  * Found unconnected internal register X and it is trimmed from A to B bits
#  * Sequential element is unused and will be removed from module
#  * Unused sequential element X_reg was removed
#  * Design has unconnected ports
#  * Design X has port Y driven by constant 'A'
# Motivation:
# Optimization. Don't need warnings from these.
set_msg_config -new_severity INFO -id {Synth 8-3936}
set_msg_config -new_severity INFO -id {Synth 8-3332}
set_msg_config -new_severity INFO -id {Synth 8-6014}
set_msg_config -new_severity INFO -id {Synth 8-3331}
set_msg_config -new_severity INFO -id {Synth 8-3917}

# Message: Ignoring unsynthesizable construct: dynamic assertion
# Motivation: Expected behavior. Dynamic assertions are used for simulation.
#             Vivado will ignore them.
set_msg_config -new_severity INFO -id {Synth 8-312}

# Message: Use of 'set_false_path' with '-hold' is not supported by synthesis.
# Motivation: Expected behavior. Will work in implementation.
set_msg_config -new_severity INFO -id {Designutils 20-1567}

# Message: Could not find module 'X'. The XDC file X.tcl will not be read for this module.
# Motivation: Expected when not using every single entity that has scoped constraints.
set_msg_config -new_severity INFO -id {Designutils 20-1281}

# Message: RAM A_reg from Abstract Data Type (record/struct) for this pattern/configuration
#          is not supported. This will most likely be implemented in registers.
# Motivation: Appears a lot when using records.
set_msg_config -new_severity INFO -id {Synth 8-5858}
