# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Example on how to raise (or, for that matter, lower) severity of some Vivado messages in your
# FPGA project.
# This file should be included as a TCL source in the Vivado project.
#
# The rules in this file make sense for the way the tsfpga maintainers develop FPGA code.
# --------------------------------------------------------------------------------------------------

puts "Applying example vivado message rules"


# --------------------------------------------------------------------------------------------------
# Upgrade to ERROR.
# --------------------------------------------------------------------------------------------------

# In the original Vivado messages rules we raise this to CRITICAL WARNING.
# But, the way we design FPGA code, these should in reality be an ERROR.
set_msg_config -new_severity "ERROR" -id "Synth 8-5863"
set_msg_config -new_severity "ERROR" -id "Synth 8-327"

# Message: Tying undriven pin to a constant.
# Motivation: An undriven pin that is used, is probably a mistake in the code.
set_msg_config -new_severity "ERROR" -id "Synth 8-3295"

# Message: Terminal has IOB constraint set to TRUE, but it is either not
#     connected to a FLOP element or the connected FLOP element could not be brought into the I/O.
# Motivation: This warning appears only if we have specifically instructed the tool to use IOB,
#     in which case failure to achieve that is an error.
set_msg_config -new_severity "ERROR" -id "Place 30-722"

# Couple of messages related to multi-driver nets or pins.
# Motivation: Driving from multiple sources is in most cases a mistake in the code.
#     We do our best to avoid this already by always using unresolved types.
#     Perhaps there is a use case out there in some exotic design, hence we keep the message raise
#     of this here in the example.
set_msg_config -new_severity "ERROR" -id "Opt 31-80"
set_msg_config -new_severity "ERROR" -id "Route 35-14"
set_msg_config -new_severity "ERROR" -id "Synth 8-6859"
set_msg_config -new_severity "ERROR" -id "Synth 8-3352"
set_property "SEVERITY" "ERROR" [get_drc_checks "MDRV-1"]

# Message: Case statement has an input that will never be executed.
# Motivation: Probably caused by a mistake in the code.
#     Can lead to undefined behavior.
set_msg_config -new_severity "ERROR" -id "Synth 8-153"

# Message: Assigned value in logic is out of range.
# Motivation: Probably caused by a mistake in the code, or setting an invalid generic value.
#     Can lead to undefined behavior or a difference in simulation/synthesis behavior.
set_msg_config -new_severity "ERROR" -id "Synth 8-3512"

# Message: Duplicate entities/files found in the same library.
# Motivation: Something has been done wrong in the project flow or the naming of files.
set_msg_config -new_severity "ERROR" -id "filemgmt 20-1318"

# Message: Duplicate IP found.
# Motivation: Something has been done wrong in the project flow or the naming of files.
set_msg_config -new_severity "ERROR" -id "IP_Flow 19-1663"

# Message: Failed to register IP shared directory path.
# Motivation: Using IP cache saves us a lot of time in builds, so we want to know if that fails.
set_msg_config -new_severity "ERROR" -id "IP_Flow 19-11772"

# Message: Port(s) exceed allowable noise margins.
# Motivation: Simultaneous switching outputs (SSOs) analysis has found that a bank has too much
#     activity, and there will be an unacceptable level of noise on one or more pins.
set_msg_config -new_severity "ERROR" -id "Designutils 20-923"

# Message: Cell is not a supported primitive for part. Instance will be treated as a black box,
#     not an architecture primitive.
# Motivation: Instantiation of a primitive that is not available for the current device is an error.
#     It is unclear what Vivado will do with this, but it is likely to lead to undefined behavior.
set_msg_config -new_severity "ERROR" -id "Netlist 29-180"

# Message: Cannot set LOC property of differential pair ports.
# Motivation: Design will not work as intended when this is the case.
set_msg_config -new_severity "ERROR" -id "Vivado 12-1411"

# Message: MMCM or PLL VCO frequency out of range.
# Motivation: Design will not work as intended when this is the case.
set_property "SEVERITY" "ERROR" [get_drc_checks "AVAL-46"]

# Message: Syntax error.
# Motivation: Quite a general message, but it definitely implies an error.
set_msg_config -new_severity "ERROR" -id "HDL 9-806"
