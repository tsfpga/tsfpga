-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity test_proj_top is
  port (
    clk : in std_ulogic;
    a : in unsigned(17 downto 0);
    b : in unsigned(17 downto 0);
    result : out unsigned(35 downto 0) := (others => '0')
  );
end entity;

architecture a of test_proj_top is
begin

  main : process
  begin
    wait until rising_edge(clk);
    result <= a * b;
  end process;

end architecture;
