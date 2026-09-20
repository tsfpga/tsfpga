// -------------------------------------------------------------------------------------------------
// Copyright (c) Lukas Vik. All rights reserved.
//
// This file is part of the tsfpga project, a project platform for modern FPGA development.
// https://tsfpga.com
// https://github.com/tsfpga/tsfpga
// -------------------------------------------------------------------------------------------------

module test_proj_top #(
    parameter WIDTH = 4
) (
    input  wire clk,
    input  wire increment,
    output wire [WIDTH-1:0] count
);

  reg [WIDTH-1:0] count_int = 0;

  always @(posedge clk) begin
    if (increment) begin
      count_int <= count_int + 1;
    end
  end

  assign count = count_int;

endmodule
