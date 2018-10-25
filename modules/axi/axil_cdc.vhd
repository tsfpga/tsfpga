-- @brief Clock crossing of an AXI-Lite bus

library ieee;
use ieee.std_logic_1164.all;

library fifo;

use work.axil_pkg.all;
use work.axi_pkg.all;


entity axil_cdc is
  generic (
    data_width : integer
  );
  port (
    clk_input : in std_logic;
    input_m2s : in axil_m2s_t;
    input_s2m : out axil_s2m_t := axil_s2m_init;
    --
    clk_output : in std_logic;
    output_m2s : out axil_m2s_t := axil_m2s_init;
    output_s2m : in axil_s2m_t
  );
end entity;

architecture a of axil_cdc is

  constant fifo_depth : integer := 16;

begin


  ------------------------------------------------------------------------------
  aw_afifo_inst : entity fifo.afifo
    generic map (
      width => axil_m2s_a_sz,
      depth => fifo_depth
    )
    port map(
      clk_read => clk_output,
      read_ready => output_s2m.write.aw.ready,
      read_valid => output_m2s.write.aw.valid,
      read_data => output_m2s.write.aw.addr,
      --
      clk_write => clk_input,
      write_ready => input_s2m.write.aw.ready,
      write_valid => input_m2s.write.aw.valid,
      write_data => input_m2s.write.aw.addr
    );


  ------------------------------------------------------------------------------
  w_block : block
    constant w_width : integer := axil_m2s_w_sz(data_width);
    signal input_m2s_w, output_m2s_w : std_logic_vector(w_width - 1 downto 0);
  begin

    output_m2s.write.w.data <= to_axil_m2s_w(output_m2s_w, data_width).data;
    output_m2s.write.w.strb <= to_axil_m2s_w(output_m2s_w, data_width).strb;
    input_m2s_w <= to_slv(input_m2s.write.w, data_width);

    w_afifo_inst : entity fifo.afifo
      generic map (
        width => w_width,
        depth => fifo_depth
      )
      port map(
        clk_read => clk_output,
        read_ready => output_s2m.write.w.ready,
        read_valid => output_m2s.write.w.valid,
        read_data => output_m2s_w,
        --
        clk_write => clk_input,
        write_ready => input_s2m.write.w.ready,
        write_valid => input_m2s.write.w.valid,
        write_data => input_m2s_w
      );
  end block;


  ------------------------------------------------------------------------------
  b_afifo_inst : entity fifo.afifo
    generic map (
      width => axi_s2m_b_sz,
      depth => fifo_depth
    )
    port map(
      clk_read => clk_input,
      read_ready => input_m2s.write.b.ready,
      read_valid => input_s2m.write.b.valid,
      read_data => input_s2m.write.b.resp,
      --
      clk_write => clk_output,
      write_ready => output_m2s.write.b.ready,
      write_valid => output_s2m.write.b.valid,
      write_data => output_s2m.write.b.resp
    );


  ------------------------------------------------------------------------------
  ar_afifo_inst : entity fifo.afifo
    generic map (
      width => axil_m2s_a_sz,
      depth => fifo_depth
    )
    port map(
      clk_read => clk_output,
      read_ready => output_s2m.read.ar.ready,
      read_valid => output_m2s.read.ar.valid,
      read_data => output_m2s.read.ar.addr,
      --
      clk_write => clk_input,
      write_ready => input_s2m.read.ar.ready,
      write_valid => input_m2s.read.ar.valid,
      write_data => input_m2s.read.ar.addr
    );


  ------------------------------------------------------------------------------
  r_block : block
    constant r_width : integer := axil_s2m_r_sz(data_width);
    signal input_s2m_r, output_s2m_r : std_logic_vector(r_width - 1 downto 0);
  begin

    input_s2m.read.r.data <= to_axil_s2m_r(input_s2m_r, data_width).data;
    input_s2m.read.r.resp <= to_axil_s2m_r(input_s2m_r, data_width).resp;
    output_s2m_r <= to_slv(output_s2m.read.r, data_width);

    r_afifo_inst : entity fifo.afifo
      generic map (
        width => r_width,
        depth => fifo_depth
      )
      port map(
        clk_read => clk_input,
        read_ready => input_m2s.read.r.ready,
        read_valid => input_s2m.read.r.valid,
        read_data => input_s2m_r,
        --
        clk_write => clk_output,
        write_ready => output_m2s.read.r.ready,
        write_valid => output_s2m.read.r.valid,
        write_data => output_s2m_r
      );
  end block;

end architecture;
