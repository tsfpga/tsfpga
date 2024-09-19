# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Complement to 'example_vivado_messages.tcl', this message will in general not work for projects
# that have IP cores, since they often contain dirty code.
# --------------------------------------------------------------------------------------------------

puts "Applying example vivado message rule"

# Message: Tying undriven pin to a constant.
# Motivation: An undriven pin that is used, is probably a mistake in the code.
set_msg_config -new_severity "ERROR" -id "Synth 8-3295"
