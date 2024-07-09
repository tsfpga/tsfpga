// -------------------------------------------------------------------------------------------------
// Copyright (c) Lukas Vik. All rights reserved.
//
// This file is part of the tsfpga project, a project platform for modern FPGA development.
// https://tsfpga.com
// https://github.com/tsfpga/tsfpga
// -------------------------------------------------------------------------------------------------


module artyz7_top_systemverilog (
  input ext_clk,
  input [0:3] led,
  output reg [23 - 1:0] dummy_output
);

`include "artyz7_top_systemverilog_header.svh"
import artyz7_top_systemverilog_pkg::*;

integer i;

always@(posedge ext_clk)
begin
  for (i = 0; i < num_dummy_output; i = i + 1) begin
    dummy_output[i] = led[i % artyz7_top_systemverilog_pkg::num_leds];
  end
end

endmodule
