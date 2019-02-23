create_ip -name mult_gen -vendor xilinx.com -library ip -version 12.0 -module_name mult_u12_u5
set_property -dict [list CONFIG.PortAType {Unsigned} CONFIG.PortAWidth {12} CONFIG.PortBType {Unsigned} CONFIG.PortBWidth {5} CONFIG.OutputWidthHigh {16}] [get_ips mult_u12_u5]

