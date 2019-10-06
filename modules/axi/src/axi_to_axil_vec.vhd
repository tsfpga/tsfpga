-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
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
    axil_vec_m2s : out axil_m2s_vec_t(axil_slaves'range);
    axil_vec_s2m : in axil_s2m_vec_t(axil_slaves'range)
  );
end entity;

architecture a of axi_to_axil_vec is
  constant data_width : integer := 32;

  signal axil_m2s : axil_m2s_t;
  signal axil_s2m : axil_s2m_t;

  signal axil_m2s_vec : axil_m2s_vec_t(axil_slaves'range);
  signal axil_s2m_vec : axil_s2m_vec_t(axil_slaves'range);
begin

  ------------------------------------------------------------------------------
  axi_to_axil_inst : entity axi.axi_to_axil
    generic map (
      data_width => data_width
    )
    port map (
      clk => clk_axi,

      axi_m2s => axi_m2s,
      axi_s2m => axi_s2m,

      axil_m2s => axil_m2s,
      axil_s2m => axil_s2m
    );


  ------------------------------------------------------------------------------
  axil_mux_inst : entity axi.axil_mux
    generic map (
      slave_addrs => axil_slaves
    )
    port map (
      clk => clk_axi,

      axil_m2s => axil_m2s,
      axil_s2m => axil_s2m,

      axil_m2s_vec => axil_m2s_vec,
      axil_s2m_vec => axil_s2m_vec
    );


    ------------------------------------------------------------------------------
    clock_domain_crossing : for slave in axil_slaves'range generate
      assign : if clocks_are_the_same(slave) generate
        axil_vec_m2s(slave) <= axil_m2s_vec(slave);
        axil_s2m_vec(slave) <= axil_vec_s2m(slave);

      else generate
        axil_cdc_inst : entity axi.axil_cdc
          generic map (
            data_width => data_width
          )
          port map (
            clk_master => clk_axi,
            master_m2s => axil_m2s_vec(slave),
            master_s2m => axil_s2m_vec(slave),
            --
            clk_slave => clk_axil_vec(slave),
            slave_m2s => axil_vec_m2s(slave),
            slave_s2m => axil_vec_s2m(slave)
          );
      end generate;
    end generate;

end architecture;
