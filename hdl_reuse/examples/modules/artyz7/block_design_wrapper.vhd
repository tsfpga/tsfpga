library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library axi;
use axi.axi_pkg.all;

library common;
use common.common_pkg.all;

use work.block_design_pkg.block_design;


entity block_design_wrapper is
  port (
    clk_m_gp0 : in std_logic;
    m_gp0_m2s : out axi_m2s_t := axi_m2s_init;
    m_gp0_s2m : in axi_s2m_t := axi_s2m_init;

    pl_clk0 : out std_logic
  );
end entity;

architecture a of block_design_wrapper is
begin

  ------------------------------------------------------------------------------
  block_design_inst : if in_simulation generate
    block_design_mock_inst : entity work.block_design_mock
      port map (
        clk_m_gp0 => clk_m_gp0,
        m_gp0_m2s => m_gp0_m2s,
        m_gp0_s2m => m_gp0_s2m,

        pl_clk0 => pl_clk0
      );

  ------------------------------------------------------------------------------
  else generate
    subtype axi3_len_rng is integer range 3 downto 0;
    subtype m_gp0_id_rng is integer range 11 downto 0;
    constant m_gp0_data_width : integer := 32;
    subtype m_gp0_strb_rng is integer range axi_w_strb_sz(m_gp0_data_width) - 1 downto 0;
  begin

    ----------------------------------------------------------------------------
    block_design_inst : component block_design
      port map (
        M_AXI_GP0_araddr => m_gp0_m2s.read.ar.addr,
        M_AXI_GP0_arburst => m_gp0_m2s.read.ar.burst,
        M_AXI_GP0_arcache => open,
        M_AXI_GP0_arid => m_gp0_m2s.read.ar.id(m_gp0_id_rng),
        M_AXI_GP0_arlen => m_gp0_m2s.read.ar.len(axi3_len_rng),
        M_AXI_GP0_arlock => open,
        M_AXI_GP0_arprot => open,
        M_AXI_GP0_arqos => open,
        M_AXI_GP0_arready => m_gp0_s2m.read.ar.ready,
        M_AXI_GP0_arsize  => m_gp0_m2s.read.ar.size,
        M_AXI_GP0_arvalid => m_gp0_m2s.read.ar.valid,
        M_AXI_GP0_awaddr => m_gp0_m2s.write.aw.addr,
        M_AXI_GP0_awburst => m_gp0_m2s.write.aw.burst,
        M_AXI_GP0_awcache => open,
        M_AXI_GP0_awid => m_gp0_m2s.write.aw.id(m_gp0_id_rng),
        M_AXI_GP0_awlen => m_gp0_m2s.write.aw.len(axi3_len_rng),
        M_AXI_GP0_awlock => open,
        M_AXI_GP0_awprot => open,
        M_AXI_GP0_awqos => open,
        M_AXI_GP0_awready => m_gp0_s2m.write.aw.ready,
        M_AXI_GP0_awsize => m_gp0_m2s.write.aw.size,
        M_AXI_GP0_awvalid => m_gp0_m2s.write.aw.valid,
        M_AXI_GP0_bid => m_gp0_s2m.write.b.id(m_gp0_id_rng),
        M_AXI_GP0_bready => m_gp0_m2s.write.b.ready,
        M_AXI_GP0_bresp => m_gp0_s2m.write.b.resp,
        M_AXI_GP0_bvalid => m_gp0_s2m.write.b.valid,
        M_AXI_GP0_rdata => m_gp0_s2m.read.r.data(m_gp0_data_width - 1 downto 0),
        M_AXI_GP0_rid => m_gp0_s2m.read.r.id(m_gp0_id_rng),
        M_AXI_GP0_rlast => m_gp0_s2m.read.r.last,
        M_AXI_GP0_rready => m_gp0_m2s.read.r.ready,
        M_AXI_GP0_rresp => m_gp0_s2m.read.r.resp,
        M_AXI_GP0_rvalid => m_gp0_s2m.read.r.valid,
        M_AXI_GP0_wdata => m_gp0_m2s.write.w.data(m_gp0_data_width - 1 downto 0),
        M_AXI_GP0_wlast => m_gp0_m2s.write.w.last,
        M_AXI_GP0_wready => m_gp0_s2m.write.w.ready,
        M_AXI_GP0_wstrb => m_gp0_m2s.write.w.strb(m_gp0_strb_rng),
        M_AXI_GP0_wvalid => m_gp0_m2s.write.w.valid,
        M_AXI_GP0_ACLK => clk_m_gp0,
        FCLK_CLK0 => pl_clk0
      );
  end generate;

end architecture;
