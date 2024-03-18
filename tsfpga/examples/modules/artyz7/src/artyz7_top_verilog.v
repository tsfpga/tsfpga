// -------------------------------------------------------------------------------------------------
// Copyright (c) Lukas Vik. All rights reserved.
//
// This file is part of the tsfpga project, a project platform for modern FPGA development.
// https://tsfpga.com
// https://github.com/tsfpga/tsfpga
// -------------------------------------------------------------------------------------------------


module artyz7_top_verilog (
  input clk_ext,
  input [0:3] led,
  output reg [22 - 1:0] dummy_output
);

`include "artyz7_top_verilog_header.vh"

integer i;

always@(posedge clk_ext)
begin
  for (i = 0; i < num_leds; i = i + 1) begin
    dummy_output[i] = led[i];
  end
end

endmodule
