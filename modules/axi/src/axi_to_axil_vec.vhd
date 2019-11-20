-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Convenience wrapper for splitting and CDC'ing a register bus.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library common;
use common.addr_pkg.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;


entity axi_to_axil_vec is
  generic (
    axil_slaves : addr_and_mask_vec_t;
    clocks_are_the_same : boolean_vector(axil_slaves'range) := (others => true)
  );
  port (
    clk_axi : in std_logic;
    axi_m2s : in axi_m2s_t;
    axi_s2m : out axi_s2m_t;

    clk_axil_vec : in std_logic_vector(axil_slaves'range) := (others => '0'); -- Only need to set if different from axi_clk
    axil_m2s_vec : out axil_m2s_vec_t(axil_slaves'range);
    axil_s2m_vec : in axil_s2m_vec_t(axil_slaves'range)
  );
end entity;

architecture a of axi_to_axil_vec is

  signal axil_m2s : axil_m2s_t;
  signal axil_s2m : axil_s2m_t;

begin

  ------------------------------------------------------------------------------
  axi_to_axil_inst : entity work.axi_to_axil
    generic map (
      data_width => 32
    )
    port map (
      clk => clk_axi,

      axi_m2s => axi_m2s,
      axi_s2m => axi_s2m,

      axil_m2s => axil_m2s,
      axil_s2m => axil_s2m
    );


  ------------------------------------------------------------------------------
  axil_to_vec_inst : entity work.axil_to_vec
    generic map (
      axil_slaves => axil_slaves,
      clocks_are_the_same => clocks_are_the_same
    )
    port map (
      clk_axil => clk_axi,
      axil_m2s => axil_m2s,
      axil_s2m => axil_s2m,

      clk_axil_vec => clk_axil_vec,
      axil_m2s_vec => axil_m2s_vec,
      axil_s2m_vec => axil_s2m_vec
    );

end architecture;
