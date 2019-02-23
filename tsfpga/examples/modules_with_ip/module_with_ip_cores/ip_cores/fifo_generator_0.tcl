create_ip -name fifo_generator -vendor xilinx.com -library ip -version 13.2 -module_name fifo_generator_0
set_property -dict [list CONFIG.Input_Data_Width {24} CONFIG.Output_Data_Width {24}] [get_ips fifo_generator_0]

