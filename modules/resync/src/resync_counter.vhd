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
use ieee.numeric_std.all;

library common;
use common.attribute_pkg.all;

library math;
use math.math_pkg.all;


entity resync_counter is
  generic (
    width : positive;
    default_value   : unsigned(width - 1 downto 0) := (others => '0');
    pipeline_output : boolean := false
    );
  port (
    clk_in     : in std_logic;
    counter_in : in unsigned(default_value'range);

    clk_out     : in std_logic;
    counter_out : out unsigned(default_value'range) := default_value
    );
end entity;

architecture a of resync_counter is
  signal counter_in_gray, counter_in_gray_p1, counter_out_gray : std_logic_vector(counter_in'range)
    := to_gray(default_value);

  attribute async_reg of counter_in_gray_p1 : signal is "true";
  attribute async_reg of counter_out_gray   : signal is "true";
begin

  clk_in_process : process
  begin
    wait until rising_edge(clk_in);
    counter_in_gray <= to_gray(counter_in);
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
