-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;

library axi_lite;
use axi_lite.axi_lite_pkg.all;

library common;
use common.common_pkg.all;

library ddr_buffer;

use work.artyz7_top_pkg.all;
use work.artyz7_register_record_pkg.all;
use work.block_design_pkg.all;


entity artyz7_top is
  generic (
    is_in_simulation : boolean := false
  );
  port (
    ext_clk : in std_ulogic;
    --# {{}}
    enable_led : in std_ulogic_vector(0 to 1);
    led : out std_ulogic_vector(0 to 3) := (others => '0');
    --# {{}}
    ddr : inout zynq7000_ddr_t;
    fixed_io : inout zynq7000_fixed_io_t
  );
end entity;

architecture a of artyz7_top is

  signal pl_clk, pl_clk_div4 : std_ulogic := '0';

  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

  signal s_hp0_m2s : axi_m2s_t := axi_m2s_init;
  signal s_hp0_s2m : axi_s2m_t := axi_s2m_init;

  signal regs_m2s : axi_lite_m2s_vec_t(regs_base_addresses'range) := (others => axi_lite_m2s_init);
  signal regs_s2m : axi_lite_s2m_vec_t(regs_base_addresses'range) := (others => axi_lite_s2m_init);

  signal ext_regs_up, pl_regs_up, pl_div4_regs_up : artyz7_regs_up_t := artyz7_regs_up_init;
  signal ext_regs_down, pl_regs_down, pl_div4_regs_down : artyz7_regs_down_t :=
    artyz7_regs_down_init;

begin

  -- Check the behavior of this function, in simulation as well as synthesis.
  assert in_simulation = is_in_simulation severity failure;


  ------------------------------------------------------------------------------
  blink0_block : block
    signal enable_blink : std_ulogic := '0';
  begin

    ------------------------------------------------------------------------------
    debounce_inst : entity common.debounce
      generic map (
        stable_count => 1024
      )
      port map (
        noisy_input => enable_led(0),
        --
        clk => pl_clk,
        stable_result => enable_blink
      );


    ------------------------------------------------------------------------------
    blink : process
      variable count : u_unsigned(27 - 1 downto 0) := (others => '0');
    begin
      wait until rising_edge(pl_clk);

      if enable_blink then
        led(0) <= count(count'high);
        count := count + 1;
      end if;
    end process;

  end block;


  ------------------------------------------------------------------------------
  blink1_block : block
    signal enable_blink : std_ulogic := '0';
  begin

    ------------------------------------------------------------------------------
    debounce_inst : entity common.debounce
      generic map (
        stable_count => 1024,
        enable_iob => false
      )
      port map (
        noisy_input => enable_led(1),
        --
        clk => ext_clk,
        stable_result => enable_blink
      );


    ------------------------------------------------------------------------------
    blink : process
      variable count : u_unsigned(27 - 1 downto 0) := (others => '0');
    begin
      wait until rising_edge(ext_clk);

      if enable_blink then
        led(1) <= count(count'high);
        count := count + 1;
      end if;
    end process;

  end block;


  ------------------------------------------------------------------------------
  regs_block : block
    -- Set up some registers to be in same clock domain as AXI port,
    -- and some to be in another clock domain.
    constant clocks_are_the_same : boolean_vector(regs_base_addresses'range) := (
      resync_ext_regs_idx => false,
      resync_pl_regs_idx => true,
      resync_pl_div4_regs_idx => false,
      ddr_buffer_regs_idx => true
    );
  begin

    ------------------------------------------------------------------------------
    axi_to_regs_inst : entity axi_lite.axi_to_axi_lite_vec
      generic map (
        base_addresses => regs_base_addresses,
        clocks_are_the_same => clocks_are_the_same
      )
      port map (
        clk_axi => pl_clk,
        axi_m2s => m_gp0_m2s,
        axi_s2m => m_gp0_s2m,
        --
        clk_axi_lite_vec(resync_ext_regs_idx) => ext_clk,
        clk_axi_lite_vec(resync_pl_regs_idx) => '0',
        clk_axi_lite_vec(resync_pl_div4_regs_idx) => pl_clk_div4,
        clk_axi_lite_vec(ddr_buffer_regs_idx) => '0',
        axi_lite_m2s_vec => regs_m2s,
        axi_lite_s2m_vec => regs_s2m
      );

    ------------------------------------------------------------------------------
    resync_ext_artyz7_reg_file_inst : entity work.artyz7_reg_file
      port map (
        clk => ext_clk,
        --
        axi_lite_m2s => regs_m2s(resync_ext_regs_idx),
        axi_lite_s2m => regs_s2m(resync_ext_regs_idx),
        --
        regs_up => ext_regs_up,
        regs_down => ext_regs_down
      );


    ------------------------------------------------------------------------------
    resync_pl_artyz7_reg_file_inst : entity work.artyz7_reg_file
      port map (
        clk => pl_clk,
        --
        axi_lite_m2s => regs_m2s(resync_pl_regs_idx),
        axi_lite_s2m => regs_s2m(resync_pl_regs_idx),
        --
        regs_up => pl_regs_up,
        regs_down => pl_regs_down
      );


    ------------------------------------------------------------------------------
    resync_pl_div4_artyz7_reg_file_inst : entity work.artyz7_reg_file
      port map (
        clk => pl_clk_div4,
        --
        axi_lite_m2s => regs_m2s(resync_pl_div4_regs_idx),
        axi_lite_s2m => regs_s2m(resync_pl_div4_regs_idx),
        --
        regs_up => pl_div4_regs_up,
        regs_down => pl_div4_regs_down
      );

  end block;


  ------------------------------------------------------------------------------
  ddr_buffer_inst : entity ddr_buffer.ddr_buffer_top
    port map (
      clk => pl_clk,
      --
      axi_read_m2s => s_hp0_m2s.read,
      axi_read_s2m => s_hp0_s2m.read,
      --
      axi_write_m2s => s_hp0_m2s.write,
      axi_write_s2m => s_hp0_s2m.write,
      --
      regs_m2s => regs_m2s(ddr_buffer_regs_idx),
      regs_s2m => regs_s2m(ddr_buffer_regs_idx)
    );


  ------------------------------------------------------------------------------
  block_design : block
  begin

    ------------------------------------------------------------------------------
    block_design_inst : entity work.block_design_wrapper
      port map (
        m_gp0_m2s => m_gp0_m2s,
        m_gp0_s2m => m_gp0_s2m,
        --
        s_hp0_m2s => s_hp0_m2s,
        s_hp0_s2m => s_hp0_s2m,
        --
        pl_clk => pl_clk,
        --
        ddr => ddr,
        fixed_io => fixed_io
      );

  end block;


  ------------------------------------------------------------------------------
  mmcm_wrapper_inst : entity work.mmcm_wrapper
    generic map (
      clk_frequency_hz => pl_clk_frequency_hz
    )
    port map (
      clk => pl_clk,
      clk_div4 => pl_clk_div4
    );


  ------------------------------------------------------------------------------
  resync_test_inst : entity work.resync_test
    port map (
      ext_clk => ext_clk,
      ext_regs_down => ext_regs_down,
      ext_regs_up => ext_regs_up,
      --
      pl_clk => pl_clk,
      pl_regs_down => pl_regs_down,
      pl_regs_up => pl_regs_up,
      --
      pl_clk_div4 => pl_clk_div4,
      pl_div4_regs_down => pl_div4_regs_down,
      pl_div4_regs_up => pl_div4_regs_up
    );


  ------------------------------------------------------------------------------
  -- Instantiate protocol checker to show that it is indeed possible to
  -- synthesize code with this instance.
  axi_stream_protocol_checker_inst : entity common.axi_stream_protocol_checker
    generic map (
      data_width => s_hp0_m2s.write.w.data'length,
      logger_name_suffix => " - artyz7_top"
    )
    port map (
      clk => pl_clk,
      --
      ready => s_hp0_s2m.write.w.ready,
      valid => s_hp0_m2s.write.w.valid,
      last => s_hp0_m2s.write.w.last,
      data => s_hp0_m2s.write.w.data,
      strobe => s_hp0_m2s.write.w.strb
    );

end architecture;
