-- @brief Resync a single bit from one clock domain to another.
-- @details This module uses a false path constraint, so it should only be used for semi static signals.

library ieee;
use ieee.std_logic_1164.all;


entity resync is
  generic (
    default_value : std_logic := '0'
  );
  port (
   data_in : in std_logic;

   clk_out : in std_logic;
   data_out : out std_logic
  );
end entity;

architecture a of resync is
  signal data_in_p1, data_out_int : std_logic := default_value;

  attribute async_reg : string;
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
