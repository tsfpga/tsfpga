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

# Check that there are no critical CDC rule violations in the design.
# List of CDC rules:
# https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/\
# Understanding-the-Clock-Domain-Crossings-Report-Rules
# If this makes your build fail on a false positive, you can waive the rule using the
# 'create_waiver' command in a (scoped) constraint file.
# Rules can be disable in general (not recommended), or for specific paths using the '-from'
# and '-to' flags (recommended).
set cdc_report [report_cdc -return_string -no_header -details -severity "Critical"]
if {[string first "Critical" ${cdc_report}] != -1} {
  puts "ERROR: Critical CDC rule violation after implementation run. See 'cdc.rpt' report."

  report_cdc -details -file "cdc.rpt"

  exit 1
}
