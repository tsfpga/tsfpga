-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief Resync a vector from one clock domain to another.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;


entity resync_slv_level is
  generic (
    default_value : std_logic := '0'
  );
  port (
   data_in : in std_logic_vector;

   clk_out : in std_logic;
   data_out : out std_logic_vector
  );
end entity;

architecture a of resync_slv_level is
begin

  resync_gen : for i in data_in'range generate
  begin
    resync_level_inst : entity work.resync_level
    generic map (
      default_value => default_value
    )
    port map (
      data_in => data_in(i),

      clk_out => clk_out,
      data_out => data_out(i)
    );
  end generate;

end architecture;
