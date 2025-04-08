# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Constraints for sink-synchronous input ports.
# See the HDL code in the 'io_constraints_top.vhd' file in the 'src' folder also for details.
# This is an example file that illustrates the constraints discussed in this article:
# https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-3-sink-synchronous-input-lukas-vik-iuxuf/
# --------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# Physical properties. Trace delays from <PCB tool>, board revision NN, YYYY-MM-DD.
# ---------------------------------------------------------------------------------
set data_pins {
  "V20"
  "W20"
  "Y18"
  "Y19"
};
set data_trace_delays_ns {
  0.891
  0.887
  0.904
  0.863
};

set clock_pin "V16";
set clock_trace_delay_ns 0.913;

# I/O bank voltage for the clock and all the data signals.
# Must be same as the peripheral device voltage.
set iostandard "LVCMOS33";

# ---------------------------------------------------------------------------------
# Timing of peripheral device. From XXXX.pdf page NN.
# Device uses a "invalid window after clock" model for setup/hold, which
# coincidentally is the exact same as the SDC notation.
# So we don't have to convert the timing numbers.
# ---------------------------------------------------------------------------------
# Time after the clock edge reaches the peripheral when its data pin might assume
# an invalid value
set peripheral_min_ns 0.1;
# Time after the clock edge reaches the peripheral when its data pin is guaranteed
# to hold a valid value.
set peripheral_max_ns 2.05;

# ---------------------------------------------------------------------------------
# Calculate pessimistic range for clock trace delay.
# ---------------------------------------------------------------------------------
set clock_trace_delay_min_ns [expr 0.9 * ${clock_trace_delay_ns}];
set clock_trace_delay_max_ns [expr 1.1 * ${clock_trace_delay_ns}];
puts "Clock trace delay between ${clock_trace_delay_min_ns} and ${clock_trace_delay_max_ns} ns.";

# ---------------------------------------------------------------------------------
# Create and constrain clock.
# ---------------------------------------------------------------------------------
set clock_port [get_ports "input_sink_synchronous_clock"];
puts "Constraining ${clock_port} to ${clock_pin}";
set_property "PACKAGE_PIN" ${clock_pin} ${clock_port};
set_property "IOSTANDARD" ${iostandard} ${clock_port};

set oddr_wrapper_inst "input_sink_synchronous_block.oddr_wrapper_inst";
set oddr_primitive_inst "${oddr_wrapper_inst}/mock_or_oddr_gen.oddr_primitive_inst";
set oddr_pin [get_pin "${oddr_primitive_inst}/oddr_gen[0].ODDR_inst/C"];
puts "Clock ODDR output pin: ${oddr_pin}.";

# Note that this is the 'output' clock. I.e. the clock on the FPGA pin. I.e. the ODDR output.
# This is not the same as the 'capture' clock that we sample input data with, which is
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

# ------------------------------------------------------------------------------
# Constrain data signals.
# ------------------------------------------------------------------------------
for {set data_index 0} {${data_index} < [llength ${data_pins}]} {incr data_index} {
  set data_pin [lindex ${data_pins} ${data_index}];
  set data_port [get_ports "input_sink_synchronous_data[${data_index}]"];
  puts "Constraining ${data_port} to ${data_pin}";
  set_property "PACKAGE_PIN" ${data_pin} ${data_port};
  set_property "IOSTANDARD" ${iostandard} ${data_port};
  set_property "IOB" "TRUE" ${data_port};

  set data_trace_delay_min_ns [expr 0.9 * [lindex ${data_trace_delays_ns} ${data_index}]];
  set data_trace_delay_max_ns [expr 1.1 * [lindex ${data_trace_delays_ns} ${data_index}]];
  puts "Trace delay between ${data_trace_delay_min_ns} and ${data_trace_delay_max_ns} ns.";

  set data_min [expr \
    ${peripheral_min_ns} + ${clock_trace_delay_min_ns} + ${data_trace_delay_min_ns}
  ];
  set data_max [expr \
    ${peripheral_max_ns} + ${clock_trace_delay_max_ns} + ${data_trace_delay_max_ns}
  ];
  puts "Final constraint: min ${data_min}, max ${data_max}.";

  set invalid_window_ns [expr ${data_max} - ${data_min}];
  set valid_window_ns [expr ${clock_period_ns} - ${invalid_window_ns}];
  puts "Valid window ${valid_window_ns} ns (invalid ${invalid_window_ns} ns).";

  # Note that constraint is applied relative to the 'output' clock (not the 'capture' clock).
  set_input_delay -clock ${clock} -min ${data_min} ${data_port};
  set_input_delay -clock ${clock} -max ${data_max} ${data_port};
}
