
package attribute_pkg is

  -- The KEEP attribute is used to prevent optimizations in which signals are optimized or absorbed into logic blocks.
  -- The attribute instructs the synthesis tool to keep the signal it was placed on, and that signal is placed in the netlist.
  -- https://www.xilinx.com/support/answers/54778.html
  attribute keep : string;

end package;
