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
  generic (
    width : positive := 8
  );
  port (
    clk : in std_ulogic;
    increment : in std_ulogic;
    count : out unsigned(width - 1 downto 0);
    flag : out std_ulogic
  );
end entity;

architecture a of test_proj_top is
  signal count_int : unsigned(width - 1 downto 0) := (others => '0');
begin

  count <= count_int;

  -- Some combinational logic that will always require LUTs to implement, regardless of how
  -- the counter's carry chain above is optimized.
  flag <=
    (count_int(0) and count_int(1))
    or (count_int(2) and not increment)
    or (count_int(3) xor count_int(0));

  main : process
  begin
    wait until rising_edge(clk);

    if increment = '1' then
      count_int <= count_int + 1;
    end if;
  end process;

end architecture;
