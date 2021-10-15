-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library xil_defaultlib;


entity multiplication is
  port (
    clk : in std_logic;
    --
    multiplicand : in unsigned(12 - 1 downto 0);
    multiplier : in unsigned(5 - 1 downto 0);
    --
    product : out unsigned(17 - 1 downto 0)
  );
end entity;

architecture a of multiplication is

begin

  mult_inst : entity xil_defaultlib.mult_u12_u5
    port map (
      clk => clk,
      a => std_logic_vector(multiplicand),
      b => std_logic_vector(multiplier),
      unsigned(p) => product
    );

end architecture;
