-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- @brief Clock crossing of an AXI-Lite bus
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library common;
use common.attribute_pkg.all;

library fifo;

use work.axil_pkg.all;
use work.axi_pkg.all;


entity axil_cdc is
  generic (
    data_width : positive;
    addr_width : positive;
    fifo_depth : positive := 16;
    ram_type : ram_style_t := ram_style_auto
  );
  port (
    clk_master : in std_logic;
    master_m2s : in axil_m2s_t;
    master_s2m : out axil_s2m_t := axil_s2m_init;
    --
    clk_slave : in std_logic;
    slave_m2s : out axil_m2s_t := axil_m2s_init;
    slave_s2m : in axil_s2m_t
  );
end entity;

architecture a of axil_cdc is

begin

  ------------------------------------------------------------------------------
  aw_afifo_inst : entity fifo.afifo
    generic map (
      width => axil_m2s_a_sz(addr_width),
      depth => fifo_depth,
      ram_type => ram_type
    )
    port map(
      clk_read => clk_slave,
      read_ready => slave_s2m.write.aw.ready,
      read_valid => slave_m2s.write.aw.valid,
      read_data => slave_m2s.write.aw.addr(addr_width - 1 downto 0),
      --
      clk_write => clk_master,
      write_ready => master_s2m.write.aw.ready,
      write_valid => master_m2s.write.aw.valid,
      write_data => master_m2s.write.aw.addr(addr_width - 1 downto 0)
    );


  ------------------------------------------------------------------------------
  w_block : block
    constant w_width : integer := axil_m2s_w_sz(data_width);
    signal master_m2s_w, slave_m2s_w : std_logic_vector(w_width - 1 downto 0);
  begin

    slave_m2s.write.w.data <= to_axil_m2s_w(slave_m2s_w, data_width).data;
    slave_m2s.write.w.strb <= to_axil_m2s_w(slave_m2s_w, data_width).strb;
    master_m2s_w <= to_slv(master_m2s.write.w, data_width);

    w_afifo_inst : entity fifo.afifo
      generic map (
        width => w_width,
        depth => fifo_depth,
        ram_type => ram_type
      )
      port map(
        clk_read => clk_slave,
        read_ready => slave_s2m.write.w.ready,
        read_valid => slave_m2s.write.w.valid,
        read_data => slave_m2s_w,
        --
        clk_write => clk_master,
        write_ready => master_s2m.write.w.ready,
        write_valid => master_m2s.write.w.valid,
        write_data => master_m2s_w
      );
  end block;


  ------------------------------------------------------------------------------
  b_afifo_inst : entity fifo.afifo
    generic map (
      width => axil_s2m_b_sz,
      depth => fifo_depth,
      ram_type => ram_type
    )
    port map(
      clk_read => clk_master,
      read_ready => master_m2s.write.b.ready,
      read_valid => master_s2m.write.b.valid,
      read_data => master_s2m.write.b.resp,
      --
      clk_write => clk_slave,
      write_ready => slave_m2s.write.b.ready,
      write_valid => slave_s2m.write.b.valid,
      write_data => slave_s2m.write.b.resp
    );


  ------------------------------------------------------------------------------
  ar_afifo_inst : entity fifo.afifo
    generic map (
      width => axil_m2s_a_sz(addr_width),
      depth => fifo_depth,
      ram_type => ram_type
    )
    port map(
      clk_read => clk_slave,
      read_ready => slave_s2m.read.ar.ready,
      read_valid => slave_m2s.read.ar.valid,
      read_data => slave_m2s.read.ar.addr(addr_width - 1 downto 0),
      --
      clk_write => clk_master,
      write_ready => master_s2m.read.ar.ready,
      write_valid => master_m2s.read.ar.valid,
      write_data => master_m2s.read.ar.addr(addr_width - 1 downto 0)
    );


  ------------------------------------------------------------------------------
  r_block : block
    constant r_width : integer := axil_s2m_r_sz(data_width);
    signal master_s2m_r, slave_s2m_r : std_logic_vector(r_width - 1 downto 0);
  begin

    master_s2m.read.r.data <= to_axil_s2m_r(master_s2m_r, data_width).data;
    master_s2m.read.r.resp <= to_axil_s2m_r(master_s2m_r, data_width).resp;
    slave_s2m_r <= to_slv(slave_s2m.read.r, data_width);

    r_afifo_inst : entity fifo.afifo
      generic map (
        width => r_width,
        depth => fifo_depth,
        ram_type => ram_type
      )
      port map(
        clk_read => clk_master,
        read_ready => master_m2s.read.r.ready,
        read_valid => master_s2m.read.r.valid,
        read_data => master_s2m_r,
        --
        clk_write => clk_slave,
        write_ready => slave_m2s.read.r.ready,
        write_valid => slave_s2m.read.r.valid,
        write_data => slave_s2m_r
      );
  end block;

end architecture;
