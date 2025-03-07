# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Constraints for source-synchronous input ports.
# --------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# Physical properties. Trace delays from <PCB tool>, board revision NN, YYYY-MM-DD.
# ---------------------------------------------------------------------------------
set data_pins {
  "R14"
  "P14"
  "N16"
  "M14"
};
set data_trace_delays_ns {
  3.021
  2.876
  2.992
  3.004
}

set clock_pin "H16";
set clock_trace_delay_ns 2.937;
# From peripheral device datasheet XXXX.pdf page NN.
set clock_period_ns 8.0;
set clock_jitter_ns 0.01;

# I/O bank voltage for the clock and all the data signals.
# Must be same as the peripheral device voltage.
set iostandard "LVCMOS33";

# ---------------------------------------------------------------------------------
# Create and constrain clock.
# ---------------------------------------------------------------------------------
set clock_port [get_ports "in_source_clock"];
puts "Constraining ${clock_port} to ${clock_pin}";
set_property "PACKAGE_PIN" ${clock_pin} ${clock_port};
set_property "IOSTANDARD" ${iostandard} ${clock_port};

set clock [
  create_clock \
    -name [get_property "NAME" ${clock_port}] \
    -period ${clock_period_ns} \
    ${clock_port}
]
puts "Created clock: ${clock}";

set_input_jitter ${clock} ${clock_jitter_ns};

set clock_trace_delay_min_ns [expr 0.9 * ${clock_trace_delay_ns}];
set clock_trace_delay_max_ns [expr 1.1 * ${clock_trace_delay_ns}];
puts "Clock trace delay between ${clock_trace_delay_min_ns} and ${clock_trace_delay_max_ns} ns.";

# ---------------------------------------------------------------------------------
# Timing of peripheral device. From XXXX.pdf page NN.
# Device uses a "valid window around clock" model, formulation #1 in the article.
# ---------------------------------------------------------------------------------
# Time before the clock edge when the peripheral data pin is guaranteed
# to hold a valid value.
set peripheral_setup_ns 1.5;
# Time after the clock edge when the peripheral data pin might assume
# an invalid value.
set peripheral_hold_ns 6.8;

set peripheral_min ${peripheral_hold_ns};
set peripheral_max [expr ${clock_period_ns} - ${peripheral_setup_ns}];

# ------------------------------------------------------------------------------
# Constrain data signals.
# ------------------------------------------------------------------------------
for {set data_index 0} {${data_index} < [llength ${data_pins}]} {incr data_index} {
  set data_pin [lindex ${data_pins} ${data_index}];
  set data_port [get_ports "in_source_data[${data_index}]"];
  puts "Constraining ${data_port} to ${data_pin}";
  set_property "PACKAGE_PIN" ${data_pin} ${data_port};
  set_property "IOSTANDARD" ${iostandard} ${data_port};
  set_property "IOB" "TRUE" ${data_port};

  # To avoid a ZHOLD_DELAY block that Vivado inserts erroneously in this particular case.
  # Should not be normally necessary.
  set_property "IOBDELAY" "NONE" [get_nets ${data_port}];

  set data_trace_delay_min_ns [expr 0.9 * [lindex ${data_trace_delays_ns} ${data_index}]];
  set data_trace_delay_max_ns [expr 1.1 * [lindex ${data_trace_delays_ns} ${data_index}]];
  puts "Trace delay between ${data_trace_delay_min_ns} and ${data_trace_delay_max_ns} ns.";

  set data_min [expr \
    ${peripheral_min} \
    + ${data_trace_delay_min_ns} \
    - ${clock_trace_delay_max_ns}
  ];
  set data_max [expr \
    ${peripheral_max} \
    + ${data_trace_delay_max_ns} \
    - ${clock_trace_delay_min_ns}
  ];
  puts "Constraint: min ${data_min}, max ${data_max}.";

  set invalid_window_ns [expr ${data_max} - ${data_min}];
  set valid_window_ns [expr ${clock_period_ns} - ${invalid_window_ns}];
  puts "Valid window ${valid_window_ns} ns (invalid ${invalid_window_ns} ns)."

  set_input_delay -clock ${clock} -min ${data_min} ${data_port};
  set_input_delay -clock ${clock} -max ${data_max} ${data_port};
}
