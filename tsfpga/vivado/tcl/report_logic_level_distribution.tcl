# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

# This call is duplicated in 'tcl.py' for cases when the synthesized design is opened.
report_design_analysis -logic_level_distribution -file "logic_level_distribution.rpt"
