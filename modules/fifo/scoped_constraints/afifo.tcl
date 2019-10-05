# ------------------------------------------------------------------------------
# Copyright (c) Lukas Vik. All rights reserved.
# ------------------------------------------------------------------------------

set read_data [get_cells memory.read_data_int_reg* -filter {PRIMITIVE_SUBGROUP==flop}]
if {${read_data} != {}} {
    # These constraints are needed when the afifo is implemented using distributed
    # ram, as there is a timing path from write clock to the read data registers.
    set clk_write [get_clocks -of_objects [get_ports clk_write]]
    set_false_path -setup -hold -from ${clk_write} -to ${read_data}
}
