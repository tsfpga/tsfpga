# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Downloaded from https://github.com/Digilent/digilent-xdc/blob/master/Arty-Z7-20-Master.xdc
# at commit 01e6bf6
# Further pins and all original names available there.
# --------------------------------------------------------------------------------------------------

# Clock Signal
set_property -dict {"PACKAGE_PIN" "H16" "IOSTANDARD" "LVCMOS33"} [get_ports "clk_ext"]
create_clock -add -name "clk_ext" -period 8.00 -waveform {0 4} [get_ports "clk_ext"]

# LEDs
set_property -dict {"PACKAGE_PIN" "R14" "IOSTANDARD" "LVCMOS33"} [get_ports "led[0]"]
set_property -dict {"PACKAGE_PIN" "P14" "IOSTANDARD" "LVCMOS33"} [get_ports "led[1]"]
set_property -dict {"PACKAGE_PIN" "N16" "IOSTANDARD" "LVCMOS33"} [get_ports "led[2]"]
set_property -dict {"PACKAGE_PIN" "M14" "IOSTANDARD" "LVCMOS33"} [get_ports "led[3]"]

# Pmod Header JA
set_property -dict {"PACKAGE_PIN" "Y18" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[0]"]
set_property -dict {"PACKAGE_PIN" "Y19" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[1]"]
set_property -dict {"PACKAGE_PIN" "Y16" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[2]"]
set_property -dict {"PACKAGE_PIN" "Y17" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[3]"]
set_property -dict {"PACKAGE_PIN" "U18" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[4]"]
set_property -dict {"PACKAGE_PIN" "U19" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[5]"]
set_property -dict {"PACKAGE_PIN" "W18" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[6]"]
set_property -dict {"PACKAGE_PIN" "W19" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[7]"]

# Pmod Header JB
set_property -dict {"PACKAGE_PIN" "Y14" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[8]"]
set_property -dict {"PACKAGE_PIN" "W14" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[9]"]
set_property -dict {"PACKAGE_PIN" "T10" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[10]"]
set_property -dict {"PACKAGE_PIN" "T11" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[11]"]
set_property -dict {"PACKAGE_PIN" "W16" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[12]"]
set_property -dict {"PACKAGE_PIN" "V16" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[13]"]
set_property -dict {"PACKAGE_PIN" "W13" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[14]"]
set_property -dict {"PACKAGE_PIN" "V12" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[15]"]

# RGB LEDs
set_property -dict {"PACKAGE_PIN" "L15" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[16]"]
set_property -dict {"PACKAGE_PIN" "G17" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[17]"]
set_property -dict {"PACKAGE_PIN" "N15" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[18]"]
set_property -dict {"PACKAGE_PIN" "G14" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[19]"]
set_property -dict {"PACKAGE_PIN" "L14" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[20]"]
set_property -dict {"PACKAGE_PIN" "M15" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[21]"]

# ChipKit Outer Digital Header
set_property -dict {"PACKAGE_PIN" "T14" "IOSTANDARD" "LVCMOS33"} [get_ports "dummy_output[22]"]
