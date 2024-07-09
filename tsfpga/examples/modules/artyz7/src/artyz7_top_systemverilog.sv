// -------------------------------------------------------------------------------------------------
// Copyright (c) Lukas Vik. All rights reserved.
//
// This file is part of the tsfpga project, a project platform for modern FPGA development.
// https://tsfpga.com
// https://github.com/tsfpga/tsfpga
// -------------------------------------------------------------------------------------------------


module artyz7_top_systemverilog (
  input ext_clk,
  output reg [0:3] led,
  input [1:0] enable_led
);

`include "artyz7_top_systemverilog_header.svh"
import artyz7_top_systemverilog_pkg::*;

integer i;

always@(posedge ext_clk)
begin
  for (i = 0; i < artyz7_top_systemverilog_pkg::num_leds; i = i + 1) begin
    led[i] = enable_led[i % num_enable_led];
  end
end

endmodule
