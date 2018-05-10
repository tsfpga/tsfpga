library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library math;
use math.math_pkg.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library vunit_lib;
use vunit_lib.bus_master_pkg.all;
use vunit_lib.axi_slave_pkg.all;
context vunit_lib.vunit_context;


entity axil_slave is
  generic (
    axi_slave : axi_slave_t;
    data_width : integer
  );
  port (
    clk : in std_logic;

    axil_read_m2s : in axil_read_m2s_t := axil_read_m2s_init;
    axil_read_s2m : out axil_read_s2m_t := axil_read_s2m_init;

    axil_write_m2s : in axil_write_m2s_t := axil_write_m2s_init;
    axil_write_s2m : out axil_write_s2m_t := axil_write_s2m_init
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

      awvalid => axil_write_m2s.aw.valid,
      awready => axil_write_s2m.aw.ready,
      awid => aid,
      awaddr => axil_write_m2s.aw.addr,
      awlen => len,
      awsize => size,
      awburst => axi_a_burst_fixed,

      wvalid => axil_write_m2s.w.valid,
      wready => axil_write_s2m.w.ready,
      wdata => axil_write_m2s.w.data(data_width - 1 downto 0),
      wstrb => axil_write_m2s.w.strb,
      wlast => '1',

      bvalid => axil_write_s2m.b.valid,
      bready => axil_write_m2s.b.ready,
      bid => bid,
      bresp => axil_write_s2m.b.resp
    );


  ------------------------------------------------------------------------------
  axi_read_slave_inst : entity vunit_lib.axi_read_slave
    generic map (
      axi_slave => axi_slave
    )
    port map (
      aclk => clk,

      arvalid => axil_read_m2s.ar.valid,
      arready => axil_read_s2m.ar.ready,
      arid => aid,
      araddr => axil_read_m2s.ar.addr,
      arlen => len,
      arsize => size,
      arburst => axi_a_burst_fixed,

      rvalid => axil_read_s2m.r.valid,
      rready => axil_read_m2s.r.ready,
      rid => rid,
      rdata => axil_read_s2m.r.data(data_width - 1 downto 0),
      rresp => axil_read_s2m.r.resp,
      rlast => open
    );

end architecture;
