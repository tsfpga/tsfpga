# Create an always failing constraint for data paths between two clocks.
# Unintentional clock crossings will fail timing with ~100 ns thanks to this.
# Clock crossing which are intentional should be handled with a "set_false_path" statement.

puts "================================================================================="
puts "constrain_clock_crossings.tcl. Constraining clocks: "
puts [get_clocks]

foreach clk1 [get_clocks] {
  foreach clk2 [get_clocks] {
    if {${clk1} != ${clk2}} {
      set_max_delay -from ${clk1} -to ${clk2} -datapath_only -100
    }
  }
}

