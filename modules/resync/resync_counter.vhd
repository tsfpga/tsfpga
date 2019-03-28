-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief Synchronize a counter value between two domains
--
-- @details This module assumes that the input counter value only increments
-- and decrements in steps of one
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library common;
use common.attribute_pkg.all;

library math;
use math.math_pkg.all;


entity resync_counter is
  generic (
    default_value   : integer := 0;
    counter_max     : integer := integer'high;
    pipeline_output : boolean := false
    );
  port (
    clk_in     : in  std_logic;
    counter_in : in integer range 0 to counter_max;

    clk_out     : in  std_logic;
    counter_out : out integer range 0 to counter_max := default_value
    );
end entity;

architecture a of resync_counter is
  constant data_width : integer := num_bits_needed(counter_max);
  signal counter_in_gray, counter_in_gray_p1, counter_out_gray : std_logic_vector(data_width-1 downto 0) := to_gray(default_value, data_width);

  attribute async_reg of counter_in_gray_p1 : signal is "true";
  attribute async_reg of counter_out_gray   : signal is "true";
begin

  assert is_power_of_two(counter_max+1) report "Counter range must be a power of two";

  clk_in_process : process
  begin
    wait until rising_edge(clk_in);
    counter_in_gray <= to_gray(counter_in, data_width);
  end process;

  clk_out_process : process
  begin
    wait until rising_edge(clk_out);
    counter_out_gray   <= counter_in_gray_p1;
    counter_in_gray_p1 <= counter_in_gray;
  end process;

  optional_output_pipe : if pipeline_output generate
    pipe : process
    begin
      wait until rising_edge(clk_out);
      counter_out <= from_gray(counter_out_gray);
    end process;
  else generate
    counter_out <= from_gray(counter_out_gray);
  end generate;

end architecture;
