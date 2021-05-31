# Downloaded from https://github.com/Digilent/digilent-xdc/blob/master/Arty-Z7-20-Master.xdc
# at commit 01e6bf6
# Further pins and all original names available there.

## Clock Signal
set_property -dict {package_pin H16 iostandard lvcmos33} [get_ports clk_ext];
create_clock -add -name clk_ext -period 8.00 -waveform {0 4} [get_ports clk_ext];

## LEDs
set_property -dict {package_pin R14 iostandard lvcmos33} [get_ports led[0]];
set_property -dict {package_pin P14 iostandard lvcmos33} [get_ports led[1]];
set_property -dict {package_pin N16 iostandard lvcmos33} [get_ports led[2]];
set_property -dict {package_pin M14 iostandard lvcmos33} [get_ports led[3]];

## Pmod Header JA
set_property -dict {package_pin Y18 iostandard lvcmos33} [get_ports dummy_output[0]];
set_property -dict {package_pin Y19 iostandard lvcmos33} [get_ports dummy_output[1]];
set_property -dict {package_pin Y16 iostandard lvcmos33} [get_ports dummy_output[2]];
set_property -dict {package_pin Y17 iostandard lvcmos33} [get_ports dummy_output[3]];
set_property -dict {package_pin U18 iostandard lvcmos33} [get_ports dummy_output[4]];
set_property -dict {package_pin U19 iostandard lvcmos33} [get_ports dummy_output[5]];
set_property -dict {package_pin W18 iostandard lvcmos33} [get_ports dummy_output[6]];
set_property -dict {package_pin W19 iostandard lvcmos33} [get_ports dummy_output[7]];

## Pmod Header JB
set_property -dict {package_pin Y14 iostandard lvcmos33} [get_ports dummy_output[8]];
set_property -dict {package_pin W14 iostandard lvcmos33} [get_ports dummy_output[9]];
set_property -dict {package_pin T10 iostandard lvcmos33} [get_ports dummy_output[10]];
set_property -dict {package_pin T11 iostandard lvcmos33} [get_ports dummy_output[11]];
set_property -dict {package_pin W16 iostandard lvcmos33} [get_ports dummy_output[12]];
set_property -dict {package_pin V16 iostandard lvcmos33} [get_ports dummy_output[13]];
set_property -dict {package_pin W13 iostandard lvcmos33} [get_ports dummy_output[14]];
set_property -dict {package_pin V12 iostandard lvcmos33} [get_ports dummy_output[15]];

## RGB LEDs
set_property -dict {package_pin L15 iostandard lvcmos33} [get_ports dummy_output[16]];
set_property -dict {package_pin G17 iostandard lvcmos33} [get_ports dummy_output[17]];
set_property -dict {package_pin N15 iostandard lvcmos33} [get_ports dummy_output[18]];
set_property -dict {package_pin G14 iostandard lvcmos33} [get_ports dummy_output[19]];
set_property -dict {package_pin L14 iostandard lvcmos33} [get_ports dummy_output[20]];
set_property -dict {package_pin M15 iostandard lvcmos33} [get_ports dummy_output[21]];
