# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Set the severity of various Vivado mesages
#
# A lot of WARNINGs from Vivado are not interesting. They should be suppressed as to not clutter
# the logs. This is achieved by lowering their severity to INFO.
#
# For some inspiration see https://github.com/slaclab/ruckus/blob/main/vivado/messages.tcl
#
# See also the file 'example_vivado_messages.tcl' for more message rules that make sense
# in some cases.
# --------------------------------------------------------------------------------------------------

puts "Applying vivado message rules"


# --------------------------------------------------------------------------------------------------
# Downgrade to INFO.
# --------------------------------------------------------------------------------------------------

# Lower from WARNING.
# Message:
#  * Found unconnected internal register X and it is trimmed from A to B bits
#  * Sequential element is unused and will be removed from module
#  * Unused sequential element X_reg was removed
#  * Design has unconnected ports
#  * Design X has port Y driven by constant 'A'
# Motivation: These are optimizations. Don't need warnings from these.
set_msg_config -new_severity "INFO" -id "Synth 8-3936"
set_msg_config -new_severity "INFO" -id "Synth 8-3332"
set_msg_config -new_severity "INFO" -id "Synth 8-6014"
set_msg_config -new_severity "INFO" -id "Synth 8-3331"
set_msg_config -new_severity "INFO" -id "Synth 8-3917"

# Lower from WARNING.
# Message: Ignoring unsynthesizable construct: dynamic assertion
# Motivation: Expected behavior. Dynamic assertions are used for simulation.
#     Vivado will ignore them.
set_msg_config -new_severity "INFO" -id "Synth 8-312"

# Lower from WARNING.
# Message: Use of 'set_false_path' with '-hold' is not supported by synthesis.
# Motivation: Expected behavior. Will work in implementation.
set_msg_config -new_severity "INFO" -id "Designutils 20-1567"

# Lower from WARNING.
# Message: Could not find module 'X'. The XDC file X.tcl will not be read for this module.
# Motivation: Expected when not using every single entity that has scoped constraints.
set_msg_config -new_severity "INFO" -id "Designutils 20-1281"

# Lower from WARNING.
# Message: RAM A_reg from Abstract Data Type (record/struct) for this pattern/configuration
#     is not supported. This will most likely be implemented in registers.
# Motivation: Appears a lot when using records.
set_msg_config -new_severity "INFO" -id "Synth 8-5858"


# --------------------------------------------------------------------------------------------------
# Upgrade to CRITICAL WARNING.
# --------------------------------------------------------------------------------------------------

# Raise from WARNING.
# Message: Implementing Library version of Mod/Rem due to signed path.
# Motivation: Likely yields greater LUT utilization and worse timing, according to the
#     warning message.
#     In most code bases this should be an ERROR.
set_msg_config -new_severity "CRITICAL WARNING" -id "Synth 8-5863"

# Raise from WARNING.
# Message: Inferring latch for variable.
# Motivation: Latches are in most cases not desired, and due to a mistake in RTL code.
#     In most code bases this should be an ERROR.
#     However, in a few cases latches are desired, so we keep it at CRITICAL WARNING.
set_msg_config -new_severity "CRITICAL WARNING" -id "Synth 8-327"


# --------------------------------------------------------------------------------------------------
# Upgrade to ERROR.
# --------------------------------------------------------------------------------------------------

# Raise from WARNING.
# Message: Signal is read in the process but is not in the sensitivity list.
# Motivation: This is an RTL error. The sensitivity list should be updated.
#     Can yield different behavior in simulation and synthesis unless fixed.
set_msg_config -new_severity "ERROR" -id "Synth 8-614"

# Raise from CRITICAL WARNING.
# Message: Command failed.
# Motivation: This message appears when the TCL command "error" is called in a
#     constraint file.
#     If we don't raise the severity, the build will continue silently.
set_msg_config -new_severity "ERROR" -id "Common 17-1548"
