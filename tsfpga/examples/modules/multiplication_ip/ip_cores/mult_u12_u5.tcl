# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://gitlab.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------

create_ip -vlnv xilinx.com:ip:mult_gen:12.0 -module_name mult_u12_u5
set_property -dict [list \
  CONFIG.PortAType "Unsigned" \
  CONFIG.PortAWidth "12" \
  CONFIG.PortBType "Unsigned" \
  CONFIG.PortBWidth "5" \
  CONFIG.OutputWidthHigh "16" \
] [get_ips mult_u12_u5]
