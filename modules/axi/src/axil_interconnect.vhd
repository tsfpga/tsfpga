-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Simple N-to-1 interconnect for connecting multiple AXI-Lite masters to one port.
--
-- Uses round-robin scheduling for the inputs.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library common;
use common.types_pkg.all;


entity axil_interconnect is
  generic(
    num_inputs : integer
  );
  port(
    clk : in std_logic;
    --
    inputs_read_m2s : in axil_read_m2s_vec_t(0 to num_inputs - 1) := (others => axil_read_m2s_init);
    inputs_read_s2m : out axil_read_s2m_vec_t(0 to num_inputs - 1) := (others => axil_read_s2m_init);
    --
    inputs_write_m2s : in axil_write_m2s_vec_t(0 to num_inputs - 1) := (others => axil_write_m2s_init);
    inputs_write_s2m : out axil_write_s2m_vec_t(0 to num_inputs - 1) := (others => axil_write_s2m_init);
    --
    output_read_m2s : out axil_read_m2s_t := axil_read_m2s_init;
    output_read_s2m : in axil_read_s2m_t := axil_read_s2m_init;
    --
    output_write_m2s : out axil_write_m2s_t := axil_write_m2s_init;
    output_write_s2m : in axil_write_s2m_t := axil_write_s2m_init
  );
end entity;

architecture a of axil_interconnect is
  signal inputs_read_axi_m2s : axi_read_m2s_vec_t(0 to num_inputs - 1) := (others => axi_read_m2s_init);
  signal inputs_read_axi_s2m : axi_read_s2m_vec_t(0 to num_inputs - 1) := (others => axi_read_s2m_init);

  signal inputs_write_axi_m2s : axi_write_m2s_vec_t(0 to num_inputs - 1) := (others => axi_write_m2s_init);
  signal inputs_write_axi_s2m : axi_write_s2m_vec_t(0 to num_inputs - 1) := (others => axi_write_s2m_init);

  signal output_read_axi_m2s : axi_read_m2s_t := axi_read_m2s_init;
  signal output_read_axi_s2m : axi_read_s2m_t := axi_read_s2m_init;

  signal output_write_axi_m2s : axi_write_m2s_t := axi_write_m2s_init;
  signal output_write_axi_s2m : axi_write_s2m_t := axi_write_s2m_init;
begin

  -- Assign to the AXI records only what is needed for the AXI-Lite function.

  ------------------------------------------------------------------------------
  inputs_read_loop : for input_idx in inputs_read_m2s'range generate
    inputs_read_axi_m2s(input_idx).ar.valid <= inputs_read_m2s(input_idx).ar.valid;
    inputs_read_axi_m2s(input_idx).ar.addr <= inputs_read_m2s(input_idx).ar.addr;

    inputs_read_s2m(input_idx).ar.ready <= inputs_read_axi_s2m(input_idx).ar.ready;

    inputs_read_axi_m2s(input_idx).r.ready <= inputs_read_m2s(input_idx).r.ready;

    inputs_read_s2m(input_idx).r.valid <= inputs_read_axi_s2m(input_idx).r.valid;
    inputs_read_s2m(input_idx).r.data <= inputs_read_axi_s2m(input_idx).r.data(inputs_read_s2m(input_idx).r.data'range);
    inputs_read_s2m(input_idx).r.resp <= inputs_read_axi_s2m(input_idx).r.resp(inputs_read_s2m(input_idx).r.resp'range);
  end generate;

  output_read_m2s.ar.valid <= output_read_axi_m2s.ar.valid;
  output_read_m2s.ar.addr <= output_read_axi_m2s.ar.addr;

  output_read_axi_s2m.ar.ready <= output_read_s2m.ar.ready;

  output_read_m2s.r.ready <= output_read_axi_m2s.r.ready;

  output_read_axi_s2m.r.valid <= output_read_s2m.r.valid;
  output_read_axi_s2m.r.data(output_read_s2m.r.data'range) <= output_read_s2m.r.data;
  output_read_axi_s2m.r.resp(output_read_s2m.r.resp'range) <= output_read_s2m.r.resp;
  -- AXI-Lite always burst length 1. Need to set last for the logic in axi_interconnect.
  output_read_axi_s2m.r.last <= '1';


  ------------------------------------------------------------------------------
  inputs_write_loop : for input_idx in inputs_read_m2s'range generate
    inputs_write_axi_m2s(input_idx).aw.valid <= inputs_write_m2s(input_idx).aw.valid;
    inputs_write_axi_m2s(input_idx).aw.addr <= inputs_write_m2s(input_idx).aw.addr;

    inputs_write_s2m(input_idx).aw.ready <= inputs_write_axi_s2m(input_idx).aw.ready;

    inputs_write_axi_m2s(input_idx).w.valid <= inputs_write_m2s(input_idx).w.valid;
    inputs_write_axi_m2s(input_idx).w.data(inputs_write_m2s(0).w.data'range) <= inputs_write_m2s(input_idx).w.data;
    inputs_write_axi_m2s(input_idx).w.strb(inputs_write_m2s(0).w.strb'range) <= inputs_write_m2s(input_idx).w.strb;

    inputs_write_s2m(input_idx).w.ready <= inputs_write_axi_s2m(input_idx).w.ready;

    inputs_write_axi_m2s(input_idx).b.ready <= inputs_write_m2s(input_idx).b.ready;

    inputs_write_s2m(input_idx).b.valid <= inputs_write_axi_s2m(input_idx).b.valid;
    inputs_write_s2m(input_idx).b.resp <= inputs_write_axi_s2m(input_idx).b.resp;
  end generate;

  output_write_m2s.aw.valid <= output_write_axi_m2s.aw.valid;
  output_write_m2s.aw.addr <= output_write_axi_m2s.aw.addr;

  output_write_axi_s2m.aw.ready <= output_write_s2m.aw.ready;

  output_write_m2s.w.valid <= output_write_axi_m2s.w.valid;
  output_write_m2s.w.data <= output_write_axi_m2s.w.data(output_write_m2s.w.data'range);
  output_write_m2s.w.strb <= output_write_axi_m2s.w.strb(output_write_m2s.w.strb'range);

  output_write_axi_s2m.w.ready <= output_write_s2m.w.ready;

  output_write_m2s.b.ready <= output_write_axi_m2s.b.ready;

  output_write_axi_s2m.b.valid <= output_write_s2m.b.valid;
  output_write_axi_s2m.b.resp <= output_write_s2m.b.resp;


  ------------------------------------------------------------------------------
  axi_interconnect_inst : entity work.axi_interconnect
    generic map (
      num_inputs => num_inputs
    )
    port map (
      clk => clk,
      --
      inputs_read_m2s => inputs_read_axi_m2s,
      inputs_read_s2m => inputs_read_axi_s2m,
      --
      inputs_write_m2s => inputs_write_axi_m2s,
      inputs_write_s2m => inputs_write_axi_s2m,
      --
      output_read_m2s => output_read_axi_m2s,
      output_read_s2m => output_read_axi_s2m,
      --
      output_write_m2s => output_write_axi_m2s,
      output_write_s2m => output_write_axi_s2m
    );

end architecture;
