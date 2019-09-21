-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief Resync a single bit from one clock domain to another.
--
-- @details The two registers will be placed in the same slice, in order to minimize MTBF.
-- This guarantees proper resynchronization of semi static "level" type signals without meta stability on rising/falling edges.
-- It can not handle "pulse" type signals. Pulses can be missed and single-cycle pulse behaviour will not work.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library common;
use common.attribute_pkg.all;


entity resync_level is
  generic (
    default_value : std_logic := '0'
  );
  port (
   data_in : in std_logic;

   clk_out : in std_logic;
   data_out : out std_logic
  );
end entity;

architecture a of resync_level is
  signal data_in_p1, data_out_int : std_logic := default_value;
  attribute async_reg of data_in_p1 : signal is "true";
  attribute async_reg of data_out_int : signal is "true";
begin

  data_out <= data_out_int;

  main : process
  begin
    wait until rising_edge(clk_out);
    data_out_int <= data_in_p1;
    data_in_p1 <= data_in;
  end process;

end architecture;
