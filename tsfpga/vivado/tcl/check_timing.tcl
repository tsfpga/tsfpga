# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# This script is applied as a hook to write_bitstream. For some reason, "[current_run]" and
# "get_property DIRECTORY" do not work properly in this situation, so we can not print the run index
# or the path.

set should_exit 0

# In minimal designs, i.e. typical FPGA starter projects, there might be no constrained paths.
# For example, input clock + input pin -> register -> output pin.
# in this case, worst negative slack is reported as "inf" in the Vivado GUI, and the SLACK property
# below is "".
# Hence we check for an empty string as well as a numeric value.
set slack [get_property "SLACK" [get_timing_paths -delay_type "min_max"]]
if {${slack} != "" && [expr {${slack} < 0}]} {
  puts "ERROR: Setup/hold timing not OK after implementation run. See 'timing_summary.rpt' report."
  report_timing_summary -file "timing_summary.rpt"

  set should_exit 1
}


if {[report_pulse_width -return_string -all_violators -no_header] != ""} {
  puts "ERROR: Pulse width timing violation after implementation run. See 'pulse_width.rpt' report."
  report_pulse_width -all_violators -file "pulse_width.rpt"

  set should_exit 1
}


if {[string first "Slack (VIOLATED)" [report_bus_skew -no_header -return_string]] != -1} {
  puts "ERROR: Bus skew constraints not met after implementation run. See 'bus_skew.rpt' report."
  report_bus_skew -file "bus_skew.rpt"

  set should_exit 1
}


# This code is duplicated in tcl.py for synthesis.
set clock_interaction_report [
  report_clock_interaction -delay_type "min_max" -no_header -return_string
]
if {[string first "(unsafe)" ${clock_interaction_report}] != -1} {
  puts "ERROR: Unhandled clock crossing after implementation run. See 'clock_interaction.rpt' and 'timing_summary.rpt' reports."
  report_clock_interaction -delay_type "min_max" -file "clock_interaction.rpt"
  report_timing_summary -file "timing_summary.rpt"

  set should_exit 1
}


if {${should_exit} eq 1} {
  exit 1
}
