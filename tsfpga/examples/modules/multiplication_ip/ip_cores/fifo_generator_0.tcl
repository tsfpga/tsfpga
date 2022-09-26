# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

create_ip -vlnv xilinx.com:ip:fifo_generator:13.2 -module_name fifo_generator_0
set_property -dict [list \
  CONFIG.Input_Data_Width "24" \
  CONFIG.Output_Data_Width "24" \
] [get_ips fifo_generator_0]
