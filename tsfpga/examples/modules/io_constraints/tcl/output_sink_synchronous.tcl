# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Constraints for sink-synchronous output ports.
# See the HDL code in the 'io_constraints_top.vhd' file in the 'src' folder also for details.
# This is an example file that illustrates the constraints discussed in this article:
# https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-6-sink-synchronous-output-lukas-vik-yod6f
# --------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# Physical properties.
# ---------------------------------------------------------------------------------
set data_pins {
  "V8"
  "W8"
  "W10"
  "W9"
};
set data_trace_delays_ns {
  1.272
  1.179
  0.991
  1.318
};

set clock_pin "Y9";
set clock_trace_delay_ns 0.779;

# From peripheral device datasheet XXXX.pdf page NN.
set clock_period_ns 8;
set clock_jitter_ns 0.01;

# I/O bank voltage for the clock and all the data signals.
# Must be same as the peripheral device voltage.
set iostandard "LVCMOS33";

# ---------------------------------------------------------------------------------
# Timing of peripheral device. From XXXX.pdf page NN.
# Device uses a "valid window around clock" model for setup/hold.
# ---------------------------------------------------------------------------------
# Time before the clock edge when data must hold a valid value.
set peripheral_setup_ns 1.4;
# Time after the clock edge when data is allowed to go invalid.
set peripheral_hold_ns 1.2;

# Converted to SDC notation per the article:
# https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-6-sink-synchronous-output-lukas-vik-yod6f
# Note that it is shifted by minus one clock period, to get reasonable values that meet timing.
set peripheral_max_ns [expr ${peripheral_setup_ns} - ${clock_period_ns}];
set peripheral_min_ns [expr - ${peripheral_hold_ns} - ${clock_period_ns}];
puts "Peripheral max ${peripheral_max_ns} ns, min ${peripheral_min_ns} ns.";

# ---------------------------------------------------------------------------------
# Timing of the gate drivers on the data signals between the FPGA and the peripheral.
# From YYYY.pdf page NN.
# ---------------------------------------------------------------------------------
set driver_latency_min_ns 1.5;
set driver_latency_max_ns 2.2;

# ---------------------------------------------------------------------------------
# Calculate pessimistic range for clock trace delay.
# ---------------------------------------------------------------------------------
set clock_trace_delay_min_ns [expr 0.9 * ${clock_trace_delay_ns}];
set clock_trace_delay_max_ns [expr 1.1 * ${clock_trace_delay_ns}];
puts "Clock trace delay between ${clock_trace_delay_min_ns} and ${clock_trace_delay_max_ns} ns.";

# ---------------------------------------------------------------------------------
# Create and constrain clock.
# ---------------------------------------------------------------------------------
set clock_port [get_ports "output_sink_synchronous_clock"];
puts "Constraining ${clock_port} to ${clock_pin}";
set_property "PACKAGE_PIN" ${clock_pin} ${clock_port};
set_property "IOSTANDARD" ${iostandard} ${clock_port};

set clock [
  create_clock \
    -name [get_property "NAME" ${clock_port}] \
    -period ${clock_period_ns} \
    ${clock_port}
];
puts "Created clock: ${clock}";

set_input_jitter ${clock} ${clock_jitter_ns};

# ------------------------------------------------------------------------------
# Constrain data signals.
# ------------------------------------------------------------------------------
for {set data_index 0} {${data_index} < [llength ${data_pins}]} {incr data_index} {
  set data_pin [lindex ${data_pins} ${data_index}];
  set data_port [get_ports "output_sink_synchronous_data[${data_index}]"];
  puts "Constraining ${data_port} to ${data_pin}";
  set_property "PACKAGE_PIN" ${data_pin} ${data_port};
  set_property "IOSTANDARD" ${iostandard} ${data_port};
  set_property "IOB" "TRUE" ${data_port};

  set data_trace_delay_min_ns [expr 0.9 * [lindex ${data_trace_delays_ns} ${data_index}]];
  set data_trace_delay_max_ns [expr 1.1 * [lindex ${data_trace_delays_ns} ${data_index}]];
  puts "Data trace delay between ${data_trace_delay_min_ns} and ${data_trace_delay_max_ns} ns.";

  set data_max [expr \
    ${peripheral_max_ns} \
    + ${data_trace_delay_max_ns} \
    + ${clock_trace_delay_max_ns} \
    + ${driver_latency_max_ns}
  ];
  set data_min [expr \
    ${peripheral_min_ns} + \
    ${data_trace_delay_min_ns} + \
    ${clock_trace_delay_min_ns} + \
    ${driver_latency_min_ns}
  ];
  puts "Final constraint: max ${data_max}, min ${data_min}.";

  set valid_window_ns [expr ${data_max} - ${data_min}];
  set invalid_window_ns [expr ${clock_period_ns} - ${valid_window_ns}];
  puts "Valid window ${valid_window_ns} ns (invalid ${invalid_window_ns} ns).";

  set_output_delay -clock ${clock} -max ${data_max} ${data_port};
  set_output_delay -clock ${clock} -min ${data_min} ${data_port};
}
