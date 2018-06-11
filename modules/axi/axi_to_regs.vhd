library ieee;
use ieee.std_logic_1164.all;

library common;
use common.addr_pkg.all;
use common.types_pkg.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;


entity axi_to_regs is
  generic (
    reg_slaves : addr_and_mask_vec_t;
    axi_and_reg_clk_are_the_same : boolean_vec_t(reg_slaves'range) := (others => true)
  );
  port (
    clk_axi : in std_logic;
    axi_m2s : in axi_m2s_t;
    axi_s2m : out axi_s2m_t;

    clk_regs : in std_logic_vector(reg_slaves'range) := (others => '0'); -- Only need to set if different from axi_clk
    regs_m2s : out axil_m2s_vec_t(reg_slaves'range);
    regs_s2m : in axil_s2m_vec_t(reg_slaves'range)
  );
end entity;

architecture a of axi_to_regs is
  constant data_width : integer := 32;

  signal axil_m2s : axil_m2s_t;
  signal axil_s2m : axil_s2m_t;

  signal axil_m2s_vec : axil_m2s_vec_t(reg_slaves'range);
  signal axil_s2m_vec : axil_s2m_vec_t(reg_slaves'range);
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
      slave_addrs => reg_slaves
    )
    port map (
      clk => clk_axi,

      axil_m2s => axil_m2s,
      axil_s2m => axil_s2m,

      axil_m2s_vec => axil_m2s_vec,
      axil_s2m_vec => axil_s2m_vec
    );


    ------------------------------------------------------------------------------
    clock_domain_crossing : for slave in reg_slaves'range generate
      assign : if axi_and_reg_clk_are_the_same(slave) generate
        regs_m2s(slave) <= axil_m2s_vec(slave);
        axil_s2m_vec(slave) <= regs_s2m(slave);

      else generate

        -- @TODO instantiate axil_cdc

      end generate;
    end generate;

end architecture;
