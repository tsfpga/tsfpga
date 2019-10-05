# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------
# Xilinx User Guide UG903 provides a good example of this type of constraints
# ------------------------------------------------------------------------------

set stable_registers [get_cells counter_in_gray_reg* -filter {PRIMITIVE_SUBGROUP==flop}]
set first_resync_registers [get_cells counter_in_gray_p1_reg* -filter {PRIMITIVE_SUBGROUP==flop}]
set clk_out [get_clocks -of_objects [get_ports clk_out]]
set clk_out_period [get_property -min PERIOD ${clk_out}]
set clk_in [get_clocks -of_objects [get_ports clk_in]]
set clk_in_period [get_property -min PERIOD ${clk_in}]
set min_clk_period [expr {((${clk_in_period} < ${clk_out_period}) ? ${clk_in_period} : ${clk_out_period})} ]

# Add bus skew constraint to make sure that multiple bit changes on one clk_in cycle are detected
# with maximum one clk_out cycle skew.
set_bus_skew ${min_clk_period} -from ${stable_registers} -to ${first_resync_registers}

# Help router by adding max delay. The bus skew constraint is the important part.
set_max_delay -datapath_only ${min_clk_period} -from ${stable_registers} -to ${first_resync_registers}
