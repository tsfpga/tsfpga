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

library vunit_lib;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;


entity axi_slave is
  generic (
    axi_slave : axi_slave_t;
    data_width : positive;
    id_width : natural := 8;
    w_fifo_depth : natural := 0
  );
  port (
    clk : in std_logic;

    axi_read_m2s : in axi_read_m2s_t := axi_read_m2s_init;
    axi_read_s2m : out axi_read_s2m_t := axi_read_s2m_init;

    axi_write_m2s : in axi_write_m2s_t := axi_write_m2s_init;
    axi_write_s2m : out axi_write_s2m_t := axi_write_s2m_init
  );
end entity;

architecture a of axi_slave is

  signal awid, bid, arid, rid : std_logic_vector(id_width - 1 downto 0);
  signal awaddr, araddr : std_logic_vector(axi_write_m2s.aw.addr'range );
  signal awlen, arlen : std_logic_vector(axi_write_m2s.aw.len'range );
  signal awsize, arsize : std_logic_vector(axi_write_m2s.aw.size'range );

begin

  write_block : block
    signal w_fifo_m2s : axi_m2s_w_t := axi_m2s_w_init;
    signal w_fifo_s2m : axi_s2m_w_t := axi_s2m_w_init;
  begin

    ------------------------------------------------------------------------------
    -- Optionally use a FIFO for the data channel. This enables a data flow pattern where
    -- the AXI slave can accept a lot of data (many bursts) before a single address transactions
    -- occurs. This can affect the behavior of your AXI master, and is a case that needs to
    -- tested sometimes.
    axi_w_fifo_inst : entity axi.axi_w_fifo
      generic map (
        data_width => data_width,
        asynchronous => false,
        depth => w_fifo_depth
      )
      port map (
        clk => clk,
        --
        input_m2s => axi_write_m2s.w,
        input_s2m => axi_write_s2m.w,
        --
        output_m2s => w_fifo_m2s,
        output_s2m => w_fifo_s2m
      );

    ------------------------------------------------------------------------------
    axi_write_slave_inst : entity vunit_lib.axi_write_slave
      generic map (
        axi_slave => axi_slave
      )
      port map (
        aclk => clk,

        awvalid => axi_write_m2s.aw.valid,
        awready => axi_write_s2m.aw.ready,
        awid => awid,
        awaddr => awaddr,
        awlen => awlen,
        awsize => awsize,
        awburst => axi_write_m2s.aw.burst,

        wvalid => w_fifo_m2s.valid,
        wready => w_fifo_s2m.ready,
        wdata => w_fifo_m2s.data(data_width - 1 downto 0),
        wstrb => w_fifo_m2s.strb,
        wlast => w_fifo_m2s.last,

        bvalid => axi_write_s2m.b.valid,
        bready => axi_write_m2s.b.ready,
        bid => bid,
        bresp => axi_write_s2m.b.resp
      );

    awid <= std_logic_vector(axi_write_m2s.aw.id(id_width - 1 downto 0));
    awaddr <= std_logic_vector(axi_write_m2s.aw.addr);
    awlen <= std_logic_vector(axi_write_m2s.aw.len);
    awsize <= std_logic_vector(axi_write_m2s.aw.size);

    axi_write_s2m.b.id(bid'range) <= unsigned(bid);
  end block;


  ------------------------------------------------------------------------------
  axi_read_slave_inst : entity vunit_lib.axi_read_slave
    generic map (
      axi_slave => axi_slave
    )
    port map (
      aclk => clk,

      arvalid => axi_read_m2s.ar.valid,
      arready => axi_read_s2m.ar.ready,
      arid => arid,
      araddr => araddr,
      arlen => arlen,
      arsize => arsize,
      arburst => axi_read_m2s.ar.burst,

      rvalid => axi_read_s2m.r.valid,
      rready => axi_read_m2s.r.ready,
      rid => rid,
      rdata => axi_read_s2m.r.data(data_width - 1 downto 0),
      rresp => axi_read_s2m.r.resp,
      rlast => axi_read_s2m.r.last
    );

  arid <= std_logic_vector(axi_read_m2s.ar.id(id_width - 1 downto 0));
  araddr <= std_logic_vector(axi_read_m2s.ar.addr);
  arlen <= std_logic_vector(axi_read_m2s.ar.len);
  arsize <= std_logic_vector(axi_read_m2s.ar.size);

  axi_read_s2m.r.id(id_width - 1 downto 0) <= unsigned(rid);

end architecture;
