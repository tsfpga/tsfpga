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
    clk_hpm0 : in std_logic;
    hpm0_m2s : out axi_m2s_t;
    hpm0_s2m : in axi_s2m_t;

    clk_hp0 : in std_logic;
    hp0_read_m2s : in axi_read_m2s_t;
    hp0_read_s2m : out axi_read_s2m_t;
    hp0_write_m2s : in axi_write_m2s_t;
    hp0_write_s2m : out axi_write_s2m_t;

    pl_clk0 : out std_logic
  );
end entity;

architecture a of block_design_wrapper is

  constant hpm0_data_width : integer := 32;
  constant hpm0_strb_width : integer := axi_w_strb_sz(hpm0_data_width);

begin

  ------------------------------------------------------------------------------
  block_design_inst : if in_simulation generate
    block_design_mock_inst : entity work.block_design_mock
      port map (
        clk_hpm0 => clk_hpm0,
        hpm0_m2s => hpm0_m2s,
        hpm0_s2m => hpm0_s2m,

        pl_clk0 => pl_clk0
      );


  ------------------------------------------------------------------------------
  else generate
    signal hpm0_araddr, hpm0_awaddr : std_logic_vector(40 -1 downto 0) := (others => '0');
    signal hp0_araddr, hp0_awaddr : std_logic_vector(49 -1 downto 0) := (others => '0');
  begin

    hp0_araddr(hp0_read_m2s.ar.addr'range) <= hp0_read_m2s.ar.addr;
    hp0_awaddr(hp0_write_m2s.aw.addr'range) <= hp0_write_m2s.aw.addr;

    hpm0_m2s.read.ar.addr <= hpm0_araddr(hpm0_m2s.read.ar.addr'range);
    hpm0_m2s.write.aw.addr <= hpm0_awaddr(hpm0_m2s.write.aw.addr'range);


    ----------------------------------------------------------------------------
    block_design_inst : component block_design
      port map (
        M_AXI_HPM0_FPD_araddr => hpm0_araddr,
        M_AXI_HPM0_FPD_arburst => hpm0_m2s.read.ar.burst,
        M_AXI_HPM0_FPD_arcache => open,
        M_AXI_HPM0_FPD_arid => open,
        M_AXI_HPM0_FPD_arlen => hpm0_m2s.read.ar.len,
        M_AXI_HPM0_FPD_arlock => open,
        M_AXI_HPM0_FPD_arprot => open,
        M_AXI_HPM0_FPD_arqos => open,
        M_AXI_HPM0_FPD_arready => hpm0_s2m.read.ar.ready,
        M_AXI_HPM0_FPD_arsize  => hpm0_m2s.read.ar.size,
        M_AXI_HPM0_FPD_aruser => open,
        M_AXI_HPM0_FPD_arvalid => hpm0_m2s.read.ar.valid,
        M_AXI_HPM0_FPD_awaddr => hpm0_awaddr,
        M_AXI_HPM0_FPD_awburst => hpm0_m2s.write.aw.burst,
        M_AXI_HPM0_FPD_awcache => open,
        M_AXI_HPM0_FPD_awid => open,
        M_AXI_HPM0_FPD_awlen => hpm0_m2s.write.aw.len,
        M_AXI_HPM0_FPD_awlock => open,
        M_AXI_HPM0_FPD_awprot => open,
        M_AXI_HPM0_FPD_awqos => open,
        M_AXI_HPM0_FPD_awready => hpm0_s2m.write.aw.ready,
        M_AXI_HPM0_FPD_awsize => hpm0_m2s.write.aw.size,
        M_AXI_HPM0_FPD_awuser => open,
        M_AXI_HPM0_FPD_awvalid => hpm0_m2s.write.aw.valid,
        M_AXI_HPM0_FPD_bid => (others => '0'),
        M_AXI_HPM0_FPD_bready => hpm0_m2s.write.b.ready,
        M_AXI_HPM0_FPD_bresp => hpm0_s2m.write.b.resp,
        M_AXI_HPM0_FPD_bvalid => hpm0_s2m.write.b.valid,
        M_AXI_HPM0_FPD_rdata => hpm0_s2m.read.r.data(hpm0_data_width - 1 downto 0),
        M_AXI_HPM0_FPD_rid => (others => '0'),
        M_AXI_HPM0_FPD_rlast => hpm0_s2m.read.r.last,
        M_AXI_HPM0_FPD_rready => hpm0_m2s.read.r.ready,
        M_AXI_HPM0_FPD_rresp => hpm0_s2m.read.r.resp,
        M_AXI_HPM0_FPD_rvalid => hpm0_s2m.read.r.valid,
        M_AXI_HPM0_FPD_wdata => hpm0_m2s.write.w.data(hpm0_data_width - 1 downto 0),
        M_AXI_HPM0_FPD_wlast => hpm0_m2s.write.w.last,
        M_AXI_HPM0_FPD_wready => hpm0_s2m.write.w.ready,
        M_AXI_HPM0_FPD_wstrb => hpm0_m2s.write.w.strb(hpm0_strb_width - 1 downto 0),
        M_AXI_HPM0_FPD_wvalid => hpm0_m2s.write.w.valid,
        S_AXI_HP0_FPD_araddr => hp0_araddr,
        S_AXI_HP0_FPD_arburst => hp0_read_m2s.ar.burst,
        S_AXI_HP0_FPD_arcache => (others => '0'),
        S_AXI_HP0_FPD_arid => (others => '0'),
        S_AXI_HP0_FPD_arlen => hp0_read_m2s.ar.len,
        S_AXI_HP0_FPD_arlock => '0',
        S_AXI_HP0_FPD_arprot => (others => '0'),
        S_AXI_HP0_FPD_arqos => (others => '0'),
        S_AXI_HP0_FPD_arready => hp0_read_s2m.ar.ready,
        S_AXI_HP0_FPD_arsize => hp0_read_m2s.ar.size,
        S_AXI_HP0_FPD_aruser => '0',
        S_AXI_HP0_FPD_arvalid => hp0_read_m2s.ar.valid,
        S_AXI_HP0_FPD_awaddr => hp0_awaddr,
        S_AXI_HP0_FPD_awburst => hp0_write_m2s.aw.burst,
        S_AXI_HP0_FPD_awcache => (others => '0'),
        S_AXI_HP0_FPD_awid => (others => '0'),
        S_AXI_HP0_FPD_awlen => hp0_write_m2s.aw.len,
        S_AXI_HP0_FPD_awlock => '0',
        S_AXI_HP0_FPD_awprot => (others => '0'),
        S_AXI_HP0_FPD_awqos => (others => '0'),
        S_AXI_HP0_FPD_awready => hp0_write_s2m.aw.ready,
        S_AXI_HP0_FPD_awsize => hp0_write_m2s.aw.size,
        S_AXI_HP0_FPD_awuser => '0',
        S_AXI_HP0_FPD_awvalid => hp0_write_m2s.aw.valid,
        S_AXI_HP0_FPD_bid => open,
        S_AXI_HP0_FPD_bready => hp0_write_m2s.b.ready,
        S_AXI_HP0_FPD_bresp => hp0_write_s2m.b.resp,
        S_AXI_HP0_FPD_bvalid => hp0_write_s2m.b.valid,
        S_AXI_HP0_FPD_rdata => hp0_read_s2m.r.data,
        S_AXI_HP0_FPD_rid => open,
        S_AXI_HP0_FPD_rlast => hp0_read_s2m.r.last,
        S_AXI_HP0_FPD_rready => hp0_read_m2s.r.ready,
        S_AXI_HP0_FPD_rresp => hp0_read_s2m.r.resp,
        S_AXI_HP0_FPD_rvalid => hp0_read_s2m.r.valid,
        S_AXI_HP0_FPD_wdata => hp0_write_m2s.w.data,
        S_AXI_HP0_FPD_wlast => hp0_write_m2s.w.last,
        S_AXI_HP0_FPD_wready => hp0_write_s2m.w.ready,
        S_AXI_HP0_FPD_wstrb => hp0_write_m2s.w.strb,
        S_AXI_HP0_FPD_wvalid => hp0_write_m2s.w.valid,
        maxihpm0_fpd_aclk => clk_hpm0,
        pl_clk0 => pl_clk0,
        saxihp0_fpd_aclk => clk_hp0
      );
  end generate;

end architecture;
