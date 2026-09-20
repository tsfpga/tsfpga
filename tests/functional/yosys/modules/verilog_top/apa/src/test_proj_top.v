//-------------------------------------------------------------------------------------------------
// Copyright (c) Lukas Vik. All rights reserved.
//
// This file is part of the tsfpga project, a project platform for modern FPGA development.
// https://tsfpga.com
// https://github.com/tsfpga/tsfpga
//-------------------------------------------------------------------------------------------------
module test_proj_top (
    input  wire clk,
    input  wire increment,
    output wire [7:0] count,
    output wire flag
);

  wire [7:0] count_a;
  wire [7:0] count_b;

  counter_a counter_a_inst (
    .clk(clk),
    .increment(increment),
    .count(count_a)
  );

  counter_b counter_b_inst (
    .clk(clk),
    .increment(increment),
    .count(count_b)
  );

  assign count = count_a;
  assign flag = count_b[7];

endmodule
