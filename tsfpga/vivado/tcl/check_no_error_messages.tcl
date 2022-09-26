# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

if {[get_msg_config -count -severity ERROR]} {
  puts "ERROR: Vivado has reported one or more ERROR messages. See build log."
  exit 1
}
