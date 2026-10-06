// -------------------------------------------------------------------------------------------------
// Copyright (c) Lukas Vik. All rights reserved.
//
// This file is part of the tsfpga project, a project platform for modern FPGA development.
// https://tsfpga.com
// https://github.com/tsfpga/tsfpga
// -------------------------------------------------------------------------------------------------

module counter (
    input  wire clk,
    input  wire increment,
    output reg [7:0] count
);

  always @(posedge clk) begin
    if (increment) begin
      count <= count + 1;
    end
  end

endmodule
