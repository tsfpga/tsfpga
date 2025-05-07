# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Constraints for source-synchronous output ports.
# See the HDL code in the 'io_constraints_top.vhd' file in the 'src' folder also for details.
# This is an example file that illustrates the constraints discussed in this article:
# https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-4-source-synchronous-output-lukas-vik-fudxc
# --------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# Physical properties. Trace delays from <PCB tool>, board revision NN, YYYY-MM-DD.
# ---------------------------------------------------------------------------------
set data_pins {
  "G14"
  "C20"
  "B20"
  "B19"
};
set data_trace_delays_ns {
  0.791
  0.787
  0.804
  0.763
};

set clock_pin "A20";
set clock_trace_delay_ns 0.713;

# I/O bank voltage for the clock and all the data signals.
# Must be same as the peripheral device voltage.
set iostandard "LVCMOS33";

# ---------------------------------------------------------------------------------
# Create and constrain output clock.
# ---------------------------------------------------------------------------------
set clock_port [get_ports "output_source_synchronous_clock"];
puts "Constraining ${clock_port} to ${clock_pin}";
set_property "PACKAGE_PIN" ${clock_pin} ${clock_port};
set_property "IOSTANDARD" ${iostandard} ${clock_port};

set oddr_wrapper_inst "output_source_synchronous_block.oddr_wrapper_inst";
set oddr_primitive_inst "${oddr_wrapper_inst}/mock_or_oddr_gen.oddr_primitive_inst";
set oddr_pin [get_pin "${oddr_primitive_inst}/oddr_gen[0].ODDR_inst/C"];
puts "Clock ODDR output pin: ${oddr_pin}.";

# Note that this is the 'output' clock. I.e. the clock on the FPGA pin. I.e. the ODDR output.
# This is not the same as the 'launch' clock that the output register is sampled with, which is
# an FPGA-internal clock.
set clock_name [
  create_generated_clock \
    -name [get_property "NAME" ${clock_port}] \
    -source ${oddr_pin} \
    -divide_by 1 \
    ${clock_port}
];
set clock [get_clocks ${clock_name}];
puts "Created clock: ${clock}.";

set clock_period_ns [get_property "PERIOD" ${clock}];
puts "Clock period: ${clock_period_ns} ns.";

# ---------------------------------------------------------------------------------
# Timing of peripheral device. From XXXX.pdf page NN.
# Device uses a "valid window around clock" model for its timing requirement.
# ---------------------------------------------------------------------------------
# Time before the clock edge when data must hold a valid value.
set peripheral_setup_ns 1.3;
# Time after the clock edge when data is allowed to go invalid.
set peripheral_hold_ns 3.7;

# Converted to SDC notation per the article:
# https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-4-source-synchronous-output-lukas-vik-fudxc
# Note that it is shifted by plus one clock period, to get reasonable values that meet timing.
set peripheral_max_ns [expr ${clock_period_ns} + ${peripheral_setup_ns}];
set peripheral_min_ns [expr ${clock_period_ns} - ${peripheral_hold_ns}];
puts "Peripheral max ${peripheral_max_ns} ns, min ${peripheral_min_ns} ns.";

# ---------------------------------------------------------------------------------
# Calculate pessimistic range for clock trace delay.
# ---------------------------------------------------------------------------------
set clock_trace_delay_min_ns [expr 0.9 * ${clock_trace_delay_ns}];
set clock_trace_delay_max_ns [expr 1.1 * ${clock_trace_delay_ns}];
puts "Clock trace delay between ${clock_trace_delay_min_ns} and ${clock_trace_delay_max_ns} ns.";

# ------------------------------------------------------------------------------
# Apply attribute to the phase-shifting MMCM that creates the launch clock.
# Recommended when introducing skew between two clocks to meet timing.
# https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/MMCM/PLL-Phase-Shift-Modes
# ------------------------------------------------------------------------------
set mmcm_wrapper_inst "output_source_synchronous_block.mmcm_wrapper_inst";
set mmcm_primitive_inst "${mmcm_wrapper_inst}/mmcm_block.mock_or_mmcm_gen.mmcm_primitive_inst";
set mmcm_inst [get_cells "${mmcm_primitive_inst}/MMCME2_ADV_inst"];
puts "MMCM instance: ${mmcm_inst}";

set_property "PHASESHIFT_MODE" "LATENCY" ${mmcm_inst};

# ------------------------------------------------------------------------------
# Constrain data signals.
# ------------------------------------------------------------------------------
for {set data_index 0} {${data_index} < [llength ${data_pins}]} {incr data_index} {
  set data_pin [lindex ${data_pins} ${data_index}];
  set data_port [get_ports "output_source_synchronous_data[${data_index}]"];
  puts "Constraining ${data_port} to ${data_pin}";
  set_property "PACKAGE_PIN" ${data_pin} ${data_port};
  set_property "IOSTANDARD" ${iostandard} ${data_port};
  set_property "IOB" "TRUE" ${data_port};

  set data_trace_delay_min_ns [expr 0.9 * [lindex ${data_trace_delays_ns} ${data_index}]];
  set data_trace_delay_max_ns [expr 1.1 * [lindex ${data_trace_delays_ns} ${data_index}]];
  puts "Trace delay between ${data_trace_delay_min_ns} and ${data_trace_delay_max_ns} ns.";

  set data_max [expr \
    ${peripheral_max_ns} + ${data_trace_delay_max_ns} - ${clock_trace_delay_min_ns}
  ];
  set data_min [expr \
    ${peripheral_min_ns} + ${data_trace_delay_min_ns} - ${clock_trace_delay_max_ns}
  ];
  puts "Final constraint: max ${data_max}, min ${data_min}.";

  set valid_window_ns [expr ${data_max} - ${data_min}];
  set invalid_window_ns [expr ${clock_period_ns} - ${valid_window_ns}];
  puts "Valid window ${valid_window_ns} ns (invalid ${invalid_window_ns} ns).";

  set_output_delay -clock ${clock} -max ${data_max} ${data_port};
  set_output_delay -clock ${clock} -min ${data_min} ${data_port};
}
