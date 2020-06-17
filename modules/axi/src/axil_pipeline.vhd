-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Pipelining of an AXI-Lite bus. Uses skid buffers so that full throughput is
-- sustained.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library common;

use work.axil_pkg.all;
use work.axi_pkg.all;


entity axil_pipeline is
  generic (
    data_width : positive;
    addr_width : positive
  );
  port (
    clk : in std_logic;
    --
    master_m2s : in axil_m2s_t;
    master_s2m : out axil_s2m_t := axil_s2m_init;
    --
    slave_m2s : out axil_m2s_t := axil_m2s_init;
    slave_s2m : in axil_s2m_t
  );
end entity;

architecture a of axil_pipeline is

begin

  ------------------------------------------------------------------------------
  aw_handshake_pipeline_inst : entity common.handshake_pipeline
    generic map (
      data_width => axil_m2s_a_sz(addr_width)
    )
    port map(
      clk => clk,
      --
      input_ready => master_s2m.write.aw.ready,
      input_valid => master_m2s.write.aw.valid,
      input_data => master_m2s.write.aw.addr(addr_width - 1 downto 0),
      --
      output_ready => slave_s2m.write.aw.ready,
      output_valid => slave_m2s.write.aw.valid,
      output_data => slave_m2s.write.aw.addr(addr_width - 1 downto 0)
    );


  ------------------------------------------------------------------------------
  w_block : block
    constant w_width : integer := axil_m2s_w_sz(data_width);
    signal master_m2s_w, slave_m2s_w : std_logic_vector(w_width - 1 downto 0);
  begin

    slave_m2s.write.w.data <= to_axil_m2s_w(slave_m2s_w, data_width).data;
    slave_m2s.write.w.strb <= to_axil_m2s_w(slave_m2s_w, data_width).strb;
    master_m2s_w <= to_slv(master_m2s.write.w, data_width);

    handshake_pipeline_inst : entity common.handshake_pipeline
      generic map (
        data_width => w_width
      )
      port map(
        clk => clk,
        --
        input_ready => master_s2m.write.w.ready,
        input_valid => master_m2s.write.w.valid,
        input_data => master_m2s_w,
        --
        output_ready => slave_s2m.write.w.ready,
        output_valid => slave_m2s.write.w.valid,
        output_data => slave_m2s_w
      );
  end block;


  ------------------------------------------------------------------------------
  b_handshake_pipeline_inst : entity common.handshake_pipeline
    generic map (
      data_width => axil_s2m_b_sz
    )
    port map(
      clk => clk,
      --
      input_ready => slave_m2s.write.b.ready,
      input_valid => slave_s2m.write.b.valid,
      input_data => slave_s2m.write.b.resp,
      --
      output_ready => master_m2s.write.b.ready,
      output_valid => master_s2m.write.b.valid,
      output_data => master_s2m.write.b.resp
    );


  ------------------------------------------------------------------------------
  ar_handshake_pipeline_inst : entity common.handshake_pipeline
    generic map (
      data_width => axil_m2s_a_sz(addr_width)
    )
    port map(
      clk => clk,
      --
      input_ready => master_s2m.read.ar.ready,
      input_valid => master_m2s.read.ar.valid,
      input_data => master_m2s.read.ar.addr(addr_width - 1 downto 0),
      --
      output_ready => slave_s2m.read.ar.ready,
      output_valid => slave_m2s.read.ar.valid,
      output_data => slave_m2s.read.ar.addr(addr_width - 1 downto 0)
    );


  ------------------------------------------------------------------------------
  r_block : block
    constant r_width : integer := axil_s2m_r_sz(data_width);
    signal master_s2m_r, slave_s2m_r : std_logic_vector(r_width - 1 downto 0);
  begin

    master_s2m.read.r.data <= to_axil_s2m_r(master_s2m_r, data_width).data;
    master_s2m.read.r.resp <= to_axil_s2m_r(master_s2m_r, data_width).resp;
    slave_s2m_r <= to_slv(slave_s2m.read.r, data_width);

    handshake_pipeline_inst : entity common.handshake_pipeline
      generic map (
        data_width => r_width
      )
      port map(
        clk => clk,
        --
        input_ready => slave_m2s.read.r.ready,
        input_valid => slave_s2m.read.r.valid,
        input_data => slave_s2m_r,
        --
        output_ready => master_m2s.read.r.ready,
        output_valid => master_s2m.read.r.valid,
        output_data => master_s2m_r
      );
  end block;

end architecture;
