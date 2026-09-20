---------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
---------------------------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity counter_b is
  port (
    clk : in std_ulogic;
    increment : in std_ulogic;
    count : out std_ulogic_vector(7 downto 0)
  );
end entity;

architecture a of counter_b is
  signal count_int : unsigned(7 downto 0) := (others => '0');
begin

  count <= std_logic_vector(count_int);

  main : process
  begin
    wait until rising_edge(clk);

    if increment = '1' then
      count_int <= count_int + 1;
    end if;
  end process;

end architecture;
