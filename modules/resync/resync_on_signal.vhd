-- @brief Sample a bit from one clock domain to another.
--
-- @details This modules does not utilize any meta stability protection.
-- It is up to the user to ensure that data_in is stable when sample_value is asserted.

library ieee;
use ieee.std_logic_1164.all;


entity resync_on_signal is
  generic (
    default_value : std_logic := '0'
  );
  port (
   data_in : in std_logic;

   clk_out : in std_logic;
   sample_value : in std_logic;
   data_out : out std_logic := default_value
  );
end entity;

architecture a of resync_on_signal is
  signal data_in_p1 : std_logic := default_value;
begin

  main : process
  begin
    wait until rising_edge(clk_out);
    if sample_value then
      data_out <= data_in_p1;
    end if;
    data_in_p1 <= data_in;
  end process;

end architecture;
