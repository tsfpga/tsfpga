
set_property -dict {package_pin Y5 iostandard lvcmos18} [get_ports clk_in]
set_property -dict {package_pin W7 iostandard lvcmos18} [get_ports input]
set_property -dict {package_pin W6 iostandard lvcmos18} [get_ports clk_out]
set_property -dict {package_pin W8 iostandard lvcmos18} [get_ports output]

# 200 MHz
create_clock -period 5 -name clk_in [get_ports clk_in]
create_clock -period 5 -name clk_out [get_ports clk_out]
