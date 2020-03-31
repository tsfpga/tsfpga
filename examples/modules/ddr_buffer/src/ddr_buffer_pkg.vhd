-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


package ddr_buffer_pkg is

  constant axi_width : integer := 64;
  constant burst_length_beats : integer := 16;

end package;
