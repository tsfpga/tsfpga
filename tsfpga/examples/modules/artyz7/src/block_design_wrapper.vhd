-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library axi;
use axi.axi_pkg.all;

library common;
use common.common_pkg.all;

use work.block_design_pkg.block_design;
use work.artyz7_top_pkg.all;


entity block_design_wrapper is
  port (
    clk_m_gp0 : in std_ulogic;
    m_gp0_m2s : out axi_m2s_t := axi_m2s_init;
    m_gp0_s2m : in axi_s2m_t;

    clk_s_hp0 : in std_ulogic;
    s_hp0_m2s : in axi_m2s_t;
    s_hp0_s2m : out axi_s2m_t := axi_s2m_init;

    pl_clk0 : out std_ulogic := '0';
    pl_clk1 : out std_ulogic := '0'
  );
end entity;

architecture a of block_design_wrapper is
begin

  ------------------------------------------------------------------------------
  block_design_gen : if in_simulation generate

    block_design_mock_inst : entity work.block_design_mock
      port map (
        clk_m_gp0 => clk_m_gp0,
        m_gp0_m2s => m_gp0_m2s,
        m_gp0_s2m => m_gp0_s2m,

        clk_s_hp0 => clk_s_hp0,
        s_hp0_m2s => s_hp0_m2s,
        s_hp0_s2m => s_hp0_s2m,

        pl_clk0 => pl_clk0,
        pl_clk1 => pl_clk1
      );


  ------------------------------------------------------------------------------
  else generate
    -- AXI3 AxLEN is narrower than AXI4. Can only represent 0-15 (between one and 16 beats).
    subtype axi3_len_rng is integer range 3 downto 0;

    subtype m_gp0_id_rng is integer range m_gp0_id_width - 1 downto 0;
    subtype m_gp0_strb_rng is integer range axi_w_strb_width(m_gp0_data_width) - 1 downto 0;

    subtype s_hp0_id_rng is integer range s_hp0_id_width - 1 downto 0;
    subtype s_hp0_data_rng is integer range s_hp0_data_width - 1 downto 0;
    subtype s_hp0_strb_rng is integer range axi_w_strb_width(s_hp0_data_width) - 1 downto 0;
  begin

    ----------------------------------------------------------------------------
    block_design_inst : component block_design
      port map (
        unsigned(M_AXI_GP0_araddr) => m_gp0_m2s.read.ar.addr(m_gp0_addr_width - 1 downto 0),
        M_AXI_GP0_arburst => m_gp0_m2s.read.ar.burst,
        M_AXI_GP0_arcache => open,
        unsigned(M_AXI_GP0_arid) => m_gp0_m2s.read.ar.id(m_gp0_id_rng),
        unsigned(M_AXI_GP0_arlen) => m_gp0_m2s.read.ar.len(axi3_len_rng),
        M_AXI_GP0_arlock => open,
        M_AXI_GP0_arprot => open,
        M_AXI_GP0_arqos => open,
        M_AXI_GP0_arready => m_gp0_s2m.read.ar.ready,
        unsigned(M_AXI_GP0_arsize) => m_gp0_m2s.read.ar.size,
        M_AXI_GP0_arvalid => m_gp0_m2s.read.ar.valid,
        unsigned(M_AXI_GP0_awaddr) => m_gp0_m2s.write.aw.addr(m_gp0_addr_width - 1 downto 0),
        M_AXI_GP0_awburst => m_gp0_m2s.write.aw.burst,
        M_AXI_GP0_awcache => open,
        unsigned(M_AXI_GP0_awid) => m_gp0_m2s.write.aw.id(m_gp0_id_rng),
        unsigned(M_AXI_GP0_awlen) => m_gp0_m2s.write.aw.len(axi3_len_rng),
        M_AXI_GP0_awlock => open,
        M_AXI_GP0_awprot => open,
        M_AXI_GP0_awqos => open,
        M_AXI_GP0_awready => m_gp0_s2m.write.aw.ready,
        unsigned(M_AXI_GP0_awsize) => m_gp0_m2s.write.aw.size,
        M_AXI_GP0_awvalid => m_gp0_m2s.write.aw.valid,
        M_AXI_GP0_bid => std_logic_vector(m_gp0_s2m.write.b.id(m_gp0_id_rng)),
        M_AXI_GP0_bready => m_gp0_m2s.write.b.ready,
        M_AXI_GP0_bresp => m_gp0_s2m.write.b.resp,
        M_AXI_GP0_bvalid => m_gp0_s2m.write.b.valid,
        M_AXI_GP0_rdata => m_gp0_s2m.read.r.data(m_gp0_data_width - 1 downto 0),
        M_AXI_GP0_rid => std_logic_vector(m_gp0_s2m.read.r.id(m_gp0_id_rng)),
        M_AXI_GP0_rlast => m_gp0_s2m.read.r.last,
        M_AXI_GP0_rready => m_gp0_m2s.read.r.ready,
        M_AXI_GP0_rresp => m_gp0_s2m.read.r.resp,
        M_AXI_GP0_rvalid => m_gp0_s2m.read.r.valid,
        M_AXI_GP0_wdata => m_gp0_m2s.write.w.data(m_gp0_data_width - 1 downto 0),
        M_AXI_GP0_wlast => m_gp0_m2s.write.w.last,
        M_AXI_GP0_wready => m_gp0_s2m.write.w.ready,
        M_AXI_GP0_wstrb => m_gp0_m2s.write.w.strb(m_gp0_strb_rng),
        M_AXI_GP0_wvalid => m_gp0_m2s.write.w.valid,
        --
        S_AXI_HP0_arready => s_hp0_s2m.read.ar.ready,
        S_AXI_HP0_awready => s_hp0_s2m.write.aw.ready,
        S_AXI_HP0_bvalid => s_hp0_s2m.write.b.valid,
        S_AXI_HP0_rlast => s_hp0_s2m.read.r.last,
        S_AXI_HP0_rvalid => s_hp0_s2m.read.r.valid,
        S_AXI_HP0_wready => s_hp0_s2m.write.w.ready,
        S_AXI_HP0_bresp => s_hp0_s2m.write.b.resp,
        S_AXI_HP0_rresp => s_hp0_s2m.read.r.resp,
        unsigned(S_AXI_HP0_bid) => s_hp0_s2m.write.b.id(s_hp0_id_rng),
        unsigned(S_AXI_HP0_rid) => s_hp0_s2m.read.r.id(s_hp0_id_rng),
        S_AXI_HP0_rdata => s_hp0_s2m.read.r.data(s_hp0_data_rng),
        S_AXI_HP0_arvalid => s_hp0_m2s.read.ar.valid,
        S_AXI_HP0_awvalid => s_hp0_m2s.write.aw.valid,
        S_AXI_HP0_bready => s_hp0_m2s.write.b.ready,
        S_AXI_HP0_rready => s_hp0_m2s.read.r.ready,
        S_AXI_HP0_wlast => s_hp0_m2s.write.w.last,
        S_AXI_HP0_wvalid => s_hp0_m2s.write.w.valid,
        S_AXI_HP0_arburst => s_hp0_m2s.read.ar.burst,
        S_AXI_HP0_arlock => axi3_a_lock_normal,
        S_AXI_HP0_arsize => std_logic_vector(s_hp0_m2s.read.ar.size),
        S_AXI_HP0_awburst => s_hp0_m2s.write.aw.burst,
        S_AXI_HP0_awlock => axi3_a_lock_normal,
        S_AXI_HP0_awsize => std_logic_vector(s_hp0_m2s.write.aw.size),
        S_AXI_HP0_arprot => axi_a_prot_unprivileged or axi_a_prot_secure or axi_a_prot_data,
        S_AXI_HP0_awprot => axi_a_prot_unprivileged or axi_a_prot_secure or axi_a_prot_data,
        S_AXI_HP0_araddr => std_logic_vector(s_hp0_m2s.read.ar.addr(s_hp0_addr_width - 1 downto 0)),
        S_AXI_HP0_awaddr =>
          std_logic_vector(s_hp0_m2s.write.aw.addr(s_hp0_addr_width - 1 downto 0)),
        S_AXI_HP0_arcache => axi_a_cache_device_non_bufferable,
        S_AXI_HP0_arlen => std_logic_vector(s_hp0_m2s.read.ar.len(axi3_len_rng)),
        S_AXI_HP0_arqos => (others => '0'), -- No QoS scheme
        S_AXI_HP0_awcache => axi_a_cache_device_non_bufferable,
        S_AXI_HP0_awlen => std_logic_vector(s_hp0_m2s.write.aw.len(axi3_len_rng)),
        S_AXI_HP0_awqos => (others => '0'), -- No QoS scheme
        S_AXI_HP0_arid => std_logic_vector(s_hp0_m2s.read.ar.id(s_hp0_id_rng)),
        S_AXI_HP0_awid => std_logic_vector(s_hp0_m2s.write.aw.id(s_hp0_id_rng)),
        S_AXI_HP0_wid => (others => '0'), -- Unused function in AXI3
        S_AXI_HP0_wdata => s_hp0_m2s.write.w.data(s_hp0_data_rng),
        S_AXI_HP0_wstrb => s_hp0_m2s.write.w.strb(s_hp0_strb_rng),
        --
        M_AXI_GP0_ACLK => clk_m_gp0,
        FCLK_CLK0 => pl_clk0,
        S_AXI_HP0_ACLK => clk_s_hp0,
        FCLK_CLK1 => pl_clk1
      );
  end generate;

end architecture;
