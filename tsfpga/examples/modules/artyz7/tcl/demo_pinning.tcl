# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# FPGA port name for the clock signal from Chip2. Used in HDL top level.
set clock_port_name "chip2_clock"
# FPGA pin name for the clock signal from Chip2.
set clock_pin "H16"
# Clock period for Chip2 (in nanoseconds).
# From datasheet XXX.pdf page YY.
set clock_period_ns 2.85
# Trace delay for the clock signal from Chip2 to FPGA.
# Given by PCB CAD tool on YYYY-MM-DD, PCB revision N.
set clock_trace_delay_ns 0.327

# FPGA port name for the data signals from Chip2. Used in HDL top level.
set data_port_name "chip2_data"
# FPGA pin names for the data signals from Chip2.
# Ascending bit index starting at 0.
set data_pins [list "D19" "D20" "L20" "L19"]
# Trace delays for the data signals from Chip2 to FPGA (in nanoseconds).
# Given by PCB CAD tool on YYYY-MM-DD, PCB revision N.
set data_trace_delays_ns [list 0.341 0.289 0.296 0.318]

# Setup time for the data signals of Chip2 (in nanoseconds).
# Meaning, the minimum time before the the rising clock edge that data signals
# are guaranteed to be stable.
# From datasheet XXX.pdf page ZZ.
# Note that this is the raw number from the datasheet, meaning this is the setup time of the
# signal directly on Chip2 pin.
# We will take trace delay differences into account later.
set chip2_data_setup_time_ns 1.2

# Hold time for the data signals of Chip2 (in nanoseconds).
# Meaning, the maximum time after the the rising clock edge that data signals
# are guaranteed to be stable.
# From datasheet XXX.pdf page ZZ.
# Note that this is the raw number from the datasheet, meaning this is the hold time of the
# signal directly on Chip2 pin.
# We will take trace delay differences into account later.
set chip2_data_hold_time_ns 0.8

# When calculating worst case trace delay skew, use a tolerance of 5%.
# Should compensate for material differences, production variations,
# temperature changes, temperature gradient across the PCB, etc.
set trace_delay_tolerance 0.05


# ==============================================================================
# Fill in data above.
# Code below, where the action happens, should not need to be modified.

# Create the clock and setup the pin.
set clock_port [get_ports ${clock_port_name}]
set_property -dict "PACKAGE_PIN ${clock_pin} IOSTANDARD LVCMOS33" ${clock_port}
create_clock -name ${clock_port_name} -period ${clock_period_ns} ${clock_port}
set clock [get_clocks ${clock_port_name}]

# Maximum and minimum tolerance factors. Will be e.g. 1.05 and 0.95.
set trace_delay_tolerance_max [expr 1 + ${trace_delay_tolerance}]
set trace_delay_tolerance_min [expr 1 - ${trace_delay_tolerance}]

# Calculate max and min range for clock trace delay.
set clock_trace_delay_max_ns [expr ${clock_trace_delay_ns} * ${trace_delay_tolerance_max}]
set clock_trace_delay_min_ns [expr ${clock_trace_delay_ns} * ${trace_delay_tolerance_min}]

# Sanity check data input above with HDL top level data vector range.
set num_data_ports [llength ${data_pins}]
if {${num_data_ports} != [llength ${data_trace_delays_ns}]} {
    error "Inconsistent data vector lengths"
}
if {${num_data_ports} != [llength [get_ports "${data_port_name}*"]]} {
    error "Inconsistent data vector lengths"
}

# for {set data_idx 0} {${data_idx} < ${num_data_ports}} {incr data_idx} {
#   # Get properties for this data signal.
#   set data [get_ports "${data_port_name}[${data_idx}]"]
#   set data_pin [lindex ${data_pins} ${data_idx}]
#   set data_trace_delay_ns [lindex ${data_trace_delays_ns} ${data_idx}]

#   # Setup the pin.
#   set_property -dict "PACKAGE_PIN ${data_pin} IOSTANDARD LVCMOS33" ${data}

#   # Calculate max and min range for data trace delay.
#   set data_trace_delay_max_ns [expr ${data_trace_delay_ns} * ${trace_delay_tolerance_max}]
#   set data_trace_delay_min_ns [expr ${data_trace_delay_ns} * ${trace_delay_tolerance_min}]

#   # Worst case for setup is when data arrives as late as theoretically possible compared to clock.
#   # I.e. when data delay is max and clock delay is min.
#   set worst_setup_skew_ns [expr ${data_trace_delay_max_ns} - ${data_trace_delay_min_ns}]

#   # Worst case for hold is when data arrives as early as theoretically possible compared to clock.
#   # I.e. when data delay is min and clock delay is max.
#   set worst_hold_skew_ns [expr ${data_trace_delay_min_ns} - ${data_trace_delay_max_ns}]

#   set setup_time_ns [expr ${chip2_data_setup_time_ns} - ${worst_setup_skew_ns}]
#   set hold_time_ns [expr ${chip2_data_hold_time_ns} - ${worst_hold_skew_ns}]

#   set_input_delay -clock ${clock} -min ${hold_time_ns} ${data}
#   set_input_delay -clock ${clock} -max ${setup_time_ns} ${data}
# }

