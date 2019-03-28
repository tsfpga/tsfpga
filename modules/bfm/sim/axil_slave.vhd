-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library math;
use math.math_pkg.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library vunit_lib;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;


entity axil_slave is
  generic (
    axi_slave : axi_slave_t;
    data_width : integer
  );
  port (
    clk : in std_logic;

    axil_m2s : in axil_m2s_t := axil_m2s_init;
    axil_s2m : out axil_s2m_t := axil_s2m_init
  );
end entity;

architecture a of axil_slave is

  signal bid, rid, aid : std_logic_vector(8 - 1 downto 0) := (others => '0'); -- Using "open" not ok in GHDL: unconstrained port "rid" must be connected

  constant len : std_logic_vector(axi_write_m2s_init.aw.len'range) := std_logic_vector(to_unsigned(0, axi_write_m2s_init.aw.len'length));
  constant size : std_logic_vector(axi_write_m2s_init.aw.size'range) := std_logic_vector(to_unsigned(log2(data_width / 8), axi_write_m2s_init.aw.size'length));

begin

  ------------------------------------------------------------------------------
  axi_write_slave_inst : entity vunit_lib.axi_write_slave
    generic map (
      axi_slave => axi_slave
    )
    port map (
      aclk => clk,

      awvalid => axil_m2s.write.aw.valid,
      awready => axil_s2m.write.aw.ready,
      awid => aid,
      awaddr => axil_m2s.write.aw.addr,
      awlen => len,
      awsize => size,
      awburst => axi_a_burst_fixed,

      wvalid => axil_m2s.write.w.valid,
      wready => axil_s2m.write.w.ready,
      wdata => axil_m2s.write.w.data(data_width - 1 downto 0),
      wstrb => axil_m2s.write.w.strb,
      wlast => '1',

      bvalid => axil_s2m.write.b.valid,
      bready => axil_m2s.write.b.ready,
      bid => bid,
      bresp => axil_s2m.write.b.resp
    );


  ------------------------------------------------------------------------------
  axi_read_slave_inst : entity vunit_lib.axi_read_slave
    generic map (
      axi_slave => axi_slave
    )
    port map (
      aclk => clk,

      arvalid => axil_m2s.read.ar.valid,
      arready => axil_s2m.read.ar.ready,
      arid => aid,
      araddr => axil_m2s.read.ar.addr,
      arlen => len,
      arsize => size,
      arburst => axi_a_burst_fixed,

      rvalid => axil_s2m.read.r.valid,
      rready => axil_m2s.read.r.ready,
      rid => rid,
      rdata => axil_s2m.read.r.data(data_width - 1 downto 0),
      rresp => axil_s2m.read.r.resp,
      rlast => open
    );

end architecture;
