-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity test_proj_top is
  port (
    clk : in std_ulogic;
    increment : in std_ulogic;
    count : out std_ulogic_vector(7 downto 0)
  );
end entity;

architecture a of test_proj_top is

  component counter is
    port (
      clk : in std_ulogic;
      increment : in std_ulogic;
      count : out std_ulogic_vector(7 downto 0)
    );
  end component;

begin

  counter_inst : counter
    port map (
      clk => clk,
      increment => increment,
      count => count
    );

end architecture;
