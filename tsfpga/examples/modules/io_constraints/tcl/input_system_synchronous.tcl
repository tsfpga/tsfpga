# --------------------------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
#
# This file is part of the tsfpga project, a project platform for modern FPGA development.
# https://tsfpga.com
# https://github.com/tsfpga/tsfpga
# --------------------------------------------------------------------------------------------------
# Constraints for system-synchronous input ports.
# See the HDL code in the 'io_constraints_top.vhd' file in the 'src' folder also for details.
# This is an example file that illustrates the constraints discussed in this article:
# https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-2-system-synchronous-input-lukas-vik-gpnkf
# --------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# Physical properties.
# ---------------------------------------------------------------------------------
set data_pins {
  "E18"
  "E19"
  "F16"
  "F17"
};
# We don't have access to any trace delay numbers from any PCB CAD tool.
# So we have to go by a visual estimate of the trace lengths, unfortunately.
# The below range is very rough and pessimistic, in both directions (as it should be
# when using this method).
set data_trace_lengths_min_cm 3;
set data_trace_lengths_max_cm 7;

set clock_pin "K17";
set clock_to_peripheral_trace_length_min_cm 1;
set clock_to_peripheral_trace_length_max_cm 4;
set clock_to_fpga_trace_length_min_cm 2;
set clock_to_fpga_trace_length_max_cm 5;

# From crystal oscillator datasheet XXXX.pdf page NN.
set clock_period_ns 8.0;
set clock_jitter_ns 0.01;

# I/O bank voltage for the clock and all the data signals.
# Must be same as the peripheral device voltage.
set iostandard "LVCMOS33";

# ---------------------------------------------------------------------------------
# Timing of peripheral device. From XXXX.pdf page NN.
# Device uses a "valid window after clock" model for setup/hold.
# ---------------------------------------------------------------------------------
# Time after the clock edge reaches the peripheral when its data pin is guaranteed
# to hold a valid value.
set peripheral_setup_ns 1.3;
# Time after the clock edge reaches the peripheral when its data pin might assume
# an invalid value.
set peripheral_hold_ns 6.3;

# Converted to SDC notation per the article:
# https://www.linkedin.com/pulse/io-timing-constraints-fpgaasic-2-system-synchronous-input-lukas-vik-gpnkf
set peripheral_min [expr ${peripheral_hold_ns} - ${clock_period_ns}];
set peripheral_max [expr ${peripheral_setup_ns}];
puts "Peripheral min ${peripheral_min} ns, max ${peripheral_max} ns.";

# ---------------------------------------------------------------------------------
# Calculate trace delays based on length estimates and a pessimistic range
# for signal propagation speed.
# ---------------------------------------------------------------------------------
# The speed at which light propagates in a vacuum, expressed in m/s.
set speed_of_light_m_s 299792458.0;
# Converted to cm/ns for convenience in the calculations below
set speed_of_light_cm_ns [expr ${speed_of_light_m_s} / pow(10.0, 7.0)];

# The speed at which electricity propagates in copper.
# https://en.wikipedia.org/wiki/Velocity_factor#Typical_velocity_factors
set propagation_speed_min_cm_ns [expr ${speed_of_light_cm_ns} * 0.3];
set propagation_speed_max_cm_ns [expr ${speed_of_light_cm_ns} * 1.0];

set data_trace_delay_min_ns [expr ${data_trace_lengths_min_cm} / ${propagation_speed_max_cm_ns}];
set data_trace_delay_max_ns [expr ${data_trace_lengths_max_cm} / ${propagation_speed_min_cm_ns}];
puts "Data trace delay between ${data_trace_delay_min_ns} and ${data_trace_delay_max_ns} ns.";

set clock_to_peripheral_trace_delay_min_ns [
  expr ${clock_to_peripheral_trace_length_min_cm} / ${propagation_speed_max_cm_ns}
];
set clock_to_peripheral_trace_delay_max_ns [
  expr ${clock_to_peripheral_trace_length_max_cm} / ${propagation_speed_min_cm_ns}
];
puts "Clock-to-peripheral trace delay between ${clock_to_peripheral_trace_delay_min_ns} and ${clock_to_peripheral_trace_delay_max_ns} ns.";

set clock_to_fpga_trace_delay_min_ns [
  expr ${clock_to_fpga_trace_length_min_cm} / ${propagation_speed_max_cm_ns}
];
set clock_to_fpga_trace_delay_max_ns [
  expr ${clock_to_fpga_trace_length_max_cm} / ${propagation_speed_min_cm_ns}
];
puts "Clock-to-FPGA trace delay between ${clock_to_fpga_trace_delay_min_ns} and ${clock_to_fpga_trace_delay_max_ns} ns.";

# ------------------------------------------------------------------------------
# Calculate data input constraints.
# ------------------------------------------------------------------------------
set data_min [expr \
  ${peripheral_min} \
  + ${data_trace_delay_min_ns} \
  + ${clock_to_peripheral_trace_delay_min_ns} \
  - ${clock_to_fpga_trace_delay_max_ns}
];
set data_max [expr \
  ${peripheral_max} \
  + ${data_trace_delay_max_ns} \
  + ${clock_to_peripheral_trace_delay_max_ns} \
  - ${clock_to_fpga_trace_delay_min_ns}
];
puts "Final constraint: min ${data_min}, max ${data_max}.";

set invalid_window_ns [expr ${data_max} - ${data_min}];
set valid_window_ns [expr ${clock_period_ns} - ${invalid_window_ns}];
puts "Valid window ${valid_window_ns} ns (invalid ${invalid_window_ns} ns).";

# ---------------------------------------------------------------------------------
# Create and constrain clock.
# ---------------------------------------------------------------------------------
set clock_port [get_ports "input_system_synchronous_clock"];
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
# Apply attribute to the phase-shifting MMCM that creates the capture clock.
# Recommended when introducing skew between two clocks to meet timing.
# # https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/MMCM/PLL-Phase-Shift-Modes
# ------------------------------------------------------------------------------
set mmcm_wrapper_inst "input_system_synchronous_block.mmcm_wrapper_inst";
set mmcm_primitive_inst "${mmcm_wrapper_inst}/mmcm_block.mock_or_mmcm_gen.mmcm_primitive_inst";
set mmcm_inst [get_cells "${mmcm_primitive_inst}/MMCME2_ADV_inst"];
puts "MMCM instance: ${mmcm_inst}";

set_property "PHASESHIFT_MODE" "LATENCY" ${mmcm_inst};

# ------------------------------------------------------------------------------
# Constrain data signals.
# ------------------------------------------------------------------------------
for {set data_index 0} {${data_index} < [llength ${data_pins}]} {incr data_index} {
  set data_pin [lindex ${data_pins} ${data_index}];
  set data_port [get_ports "input_system_synchronous_data[${data_index}]"];
  puts "Constraining ${data_port} to ${data_pin}";
  set_property "PACKAGE_PIN" ${data_pin} ${data_port};
  set_property "IOSTANDARD" ${iostandard} ${data_port};
  set_property "IOB" "TRUE" ${data_port};

  set_input_delay -clock ${clock} -min ${data_min} ${data_port};
  set_input_delay -clock ${clock} -max ${data_max} ${data_port};
}
