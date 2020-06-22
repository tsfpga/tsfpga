-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Convenience wrapper for splitting and CDC'ing a register bus.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library axi;
use axi.axil_pkg.all;

library common;
use common.addr_pkg.all;
use common.attribute_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.all;


entity axil_to_vec is
  generic (
    axil_slaves : addr_and_mask_vec_t;
    clocks_are_the_same : boolean_vector(axil_slaves'range) := (others => true);
    cdc_fifo_depth : positive := 16;
    cdc_ram_type : ram_style_t := ram_style_auto
  );
  port (
    clk_axil : in std_logic;
    axil_m2s : in axil_m2s_t;
    axil_s2m : out axil_s2m_t;

    -- Only need to set if different from axi_clk
    clk_axil_vec : in std_logic_vector(axil_slaves'range) := (others => '0');
    axil_m2s_vec : out axil_m2s_vec_t(axil_slaves'range);
    axil_s2m_vec : in axil_s2m_vec_t(axil_slaves'range)
  );
end entity;

architecture a of axil_to_vec is

  constant addr_width : positive := addr_bits_needed(axil_slaves);

  signal axil_m2s_vec_int : axil_m2s_vec_t(axil_slaves'range);
  signal axil_s2m_vec_int : axil_s2m_vec_t(axil_slaves'range);

begin

  ------------------------------------------------------------------------------
  axil_mux_inst : entity axi.axil_mux
    generic map (
      slave_addrs => axil_slaves
    )
    port map (
      clk => clk_axil,

      axil_m2s => axil_m2s,
      axil_s2m => axil_s2m,

      axil_m2s_vec => axil_m2s_vec_int,
      axil_s2m_vec => axil_s2m_vec_int
    );


    ------------------------------------------------------------------------------
    clock_domain_crossing : for slave in axil_slaves'range generate
      assign : if clocks_are_the_same(slave) generate
        axil_m2s_vec(slave) <= axil_m2s_vec_int(slave);
        axil_s2m_vec_int(slave) <= axil_s2m_vec(slave);

      else generate
        axil_cdc_inst : entity axi.axil_cdc
          generic map (
            data_width => reg_width,
            addr_width => addr_width,
            fifo_depth => cdc_fifo_depth,
            ram_type => cdc_ram_type
          )
          port map (
            clk_master => clk_axil,
            master_m2s => axil_m2s_vec_int(slave),
            master_s2m => axil_s2m_vec_int(slave),
            --
            clk_slave => clk_axil_vec(slave),
            slave_m2s => axil_m2s_vec(slave),
            slave_s2m => axil_s2m_vec(slave)
          );
      end generate;
    end generate;

end architecture;
