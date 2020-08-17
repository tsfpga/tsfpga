# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

if {[expr {[get_property SLACK [get_timing_paths -delay_type min_max]] < 0}]} {
  set run [current_run]
  set run_directory [get_property DIRECTORY ${run}]

  puts "ERROR: Timing not OK after implementation run. See timing_summary.rpt in impl run folder."
  report_timing_summary -file "timing_summary.rpt"
  exit 1
}
