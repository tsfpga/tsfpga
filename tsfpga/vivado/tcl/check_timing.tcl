# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# This script is applied as a hook to write_bitstream. For some reason, "[current_run]" and
# "get_property DIRECTORY" do not work properly in this situation, so we can not print the run index
# or the path.

set timing_error 0


if {[expr {[get_property SLACK [get_timing_paths -delay_type min_max]] < 0}]} {
  puts "ERROR: Setup/hold timing not OK after implementation run. See timing_summary.rpt report."
  report_timing_summary -file "timing_summary.rpt"

  set timing_error 1
}


if {[report_pulse_width -return_string -all_violators -no_header] != ""} {
  puts "ERROR: Pulse width timing violation after implementation run. See pulse_width.rpt report."
  report_pulse_width -all_violators -file "pulse_width.rpt"

  set timing_error 1
}


if {[regexp {Slack \(VIOLATED\)} [report_bus_skew -no_header -return_string]]} {
  puts "ERROR: Bus skew constraints not met after implementation run. See bus_skew.rpt report."
  report_bus_skew -file "bus_skew.rpt"

  set timing_error 1
}


# This code is duplicated in tcl.py for synthesis.
if {[regexp {\(unsafe\)} [report_clock_interaction -delay_type min_max -return_string]]} {
  puts "ERROR: Unhandled clock crossing after implementation run. See clock_interaction.rpt and timing_summary.rpt reports."
  report_clock_interaction -delay_type min_max -file "clock_interaction.rpt"
  report_timing_summary -file "timing_summary.rpt"

  set timing_error 1
}


if {${timing_error} eq 1} {
  exit 1
}
