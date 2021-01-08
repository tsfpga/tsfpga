-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Resync a vector from one clock domain to another.
--
-- See resync_level header for details about constraining.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;


entity resync_slv_level is
  generic (
    width : positive;
    default_value : std_logic_vector(width - 1 downto 0) := (others => '0')
  );
  port (
    clk_in : in std_logic := '0';
    data_in : in std_logic_vector(default_value'range);

    clk_out : in std_logic;
    data_out : out std_logic_vector(default_value'range) := default_value
  );
end entity;

architecture a of resync_slv_level is
begin

  resync_gen : for i in data_in'range generate
  begin
    resync_level_inst : entity work.resync_level
    generic map (
      default_value => default_value(i)
    )
    port map (
      clk_in => clk_in,
      data_in => data_in(i),

      clk_out => clk_out,
      data_out => data_out(i)
    );
  end generate;

end architecture;
