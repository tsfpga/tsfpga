# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

if {[expr {[get_property SLACK [get_timing_paths -delay_type min_max]] < 0}]} {
  set run [current_run]
  set run_directory [get_property DIRECTORY ${run}]

  puts "ERROR: Setup/hold timing not OK after implementation run. See timing_summary.rpt in impl run folder."
  report_timing_summary -file "timing_summary.rpt"
  exit 1
}
