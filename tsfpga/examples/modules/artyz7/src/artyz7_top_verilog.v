// -------------------------------------------------------------------------------------------------
// Copyright (c) Lukas Vik. All rights reserved.
//
// This file is part of the tsfpga project, a project platform for modern FPGA development.
// https://tsfpga.com
// https://github.com/tsfpga/tsfpga
// -------------------------------------------------------------------------------------------------


module artyz7_top_verilog (
  input ext_clk,
  output reg [0:3] led,
  input [1:0] enable_led
);

`include "artyz7_top_verilog_header.vh"

integer i;

always@(posedge ext_clk)
begin
  for (i = 0; i < num_leds; i = i + 1) begin
    led[i] = enable_led[i % 2];
  end
end

endmodule
