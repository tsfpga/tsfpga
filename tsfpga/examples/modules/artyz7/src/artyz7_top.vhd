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
use common.attribute_pkg.all;
use common.common_pkg.all;

library ddr_buffer;

library fifo;

library reg_file;

library resync;

use work.artyz7_top_pkg.all;
use work.artyz7_regs_pkg.all;
use work.artyz7_register_record_pkg.all;


entity artyz7_top is
  generic (
    is_in_simulation : boolean := false
  );
  port (
    clk_ext : in std_ulogic;
    --# {{}}
    enable_led : in std_ulogic_vector(0 to 1);
    led : out std_ulogic_vector(0 to 3) := (others => '0')
  );
end entity;

architecture a of artyz7_top is

  signal clk_m_gp0 : std_ulogic := '0';
  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

  signal clk_s_hp0, clk_s_hp0_div4 : std_ulogic := '0';
  signal s_hp0_m2s : axi_m2s_t := axi_m2s_init;
  signal s_hp0_s2m : axi_s2m_t := axi_s2m_init;

  signal regs_m2s : axi_lite_m2s_vec_t(regs_base_addresses'range) := (others => axi_lite_m2s_init);
  signal regs_s2m : axi_lite_s2m_vec_t(regs_base_addresses'range) := (others => axi_lite_s2m_init);

  signal hp0_regs_up, ext_regs_up : artyz7_regs_up_t := artyz7_regs_up_init;
  signal hp0_regs_down, ext_regs_down : artyz7_regs_down_t := artyz7_regs_down_init;

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
        clk => clk_m_gp0,
        stable_result => enable_blink
      );


    ------------------------------------------------------------------------------
    blink : process
      variable count : u_unsigned(27 - 1 downto 0) := (others => '0');
    begin
      wait until rising_edge(clk_m_gp0);

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
        clk => clk_s_hp0,
        stable_result => enable_blink
      );


    ------------------------------------------------------------------------------
    blink : process
      variable count : u_unsigned(27 - 1 downto 0) := (others => '0');
    begin
      wait until rising_edge(clk_s_hp0);

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
      resync_hp0_regs_idx => false, resync_ext_regs_idx => false, ddr_buffer_regs_idx => false
    );
  begin

    ------------------------------------------------------------------------------
    axi_to_regs_inst : entity axi_lite.axi_to_axi_lite_vec
      generic map (
        base_addresses => regs_base_addresses,
        clocks_are_the_same => clocks_are_the_same
      )
      port map (
        clk_axi => clk_m_gp0,
        axi_m2s => m_gp0_m2s,
        axi_s2m => m_gp0_s2m,
        --
        clk_axi_lite_vec(resync_hp0_regs_idx) => clk_s_hp0,
        clk_axi_lite_vec(resync_ext_regs_idx) => clk_ext,
        clk_axi_lite_vec(ddr_buffer_regs_idx) => clk_s_hp0,
        axi_lite_m2s_vec => regs_m2s,
        axi_lite_s2m_vec => regs_s2m
      );


    ------------------------------------------------------------------------------
    resync_hp0_artyz7_reg_file_inst : entity work.artyz7_reg_file
      port map (
        clk => clk_s_hp0,
        --
        axi_lite_m2s => regs_m2s(resync_hp0_regs_idx),
        axi_lite_s2m => regs_s2m(resync_hp0_regs_idx),
        --
        regs_up => hp0_regs_up,
        regs_down => hp0_regs_down
      );


    ------------------------------------------------------------------------------
    resync_ext_artyz7_reg_file_inst : entity work.artyz7_reg_file
      port map (
        clk => clk_ext,
        --
        axi_lite_m2s => regs_m2s(resync_ext_regs_idx),
        axi_lite_s2m => regs_s2m(resync_ext_regs_idx),
        --
        regs_up => ext_regs_up,
        regs_down => ext_regs_down
      );

  end block;


  ------------------------------------------------------------------------------
  ddr_buffer_inst : entity ddr_buffer.ddr_buffer_top
    port map (
      clk => clk_s_hp0,
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
    signal pl_clk0, pl_clk1 : std_ulogic := '0';
  begin

    clk_m_gp0 <= pl_clk0;
    clk_s_hp0 <= pl_clk1;


    ------------------------------------------------------------------------------
    block_design_inst : entity work.block_design_wrapper
      port map (
        clk_m_gp0 => clk_m_gp0,
        m_gp0_m2s => m_gp0_m2s,
        m_gp0_s2m => m_gp0_s2m,
        --
        clk_s_hp0 => clk_s_hp0,
        s_hp0_m2s => s_hp0_m2s,
        s_hp0_s2m => s_hp0_s2m,
        --
        pl_clk0 => pl_clk0,
        pl_clk1 => pl_clk1
      );

  end block;


  ------------------------------------------------------------------------------
  mmcm_wrapper_inst : entity work.mmcm_wrapper
    generic map (
      clk_frequency_hz => clk_s_hp0_frequency_hz
    )
    port map (
      clk => clk_s_hp0,
      clk_div4 => clk_s_hp0_div4
    );


  ------------------------------------------------------------------------------
  -- Build with an instance of each of the available resync block. To show that the constraints work
  -- and the build passes timing.
  -- All resync should be from internal clock to clk_ext.
  resync_test_block : block
  begin

    ------------------------------------------------------------------------------
    resync_counter_wide_no_output_register_block : block
      constant resync_idx : natural := 0;
      signal data_in, data_out : u_unsigned(16 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        -- If changed to +2, simulation should crash on assert false.
        data_in <= data_in + 1;
      end process;


      ------------------------------------------------------------------------------
      resync_counter_inst : entity resync.resync_counter
        generic map (
          width => data_in'length,
          pipeline_output => false
        )
        port map (
          clk_in => clk_s_hp0,
          counter_in => data_in,
          --
          clk_out => clk_ext,
          counter_out => data_out
        );

      ext_regs_up.resync(resync_idx).data(data_out'range) <= std_ulogic_vector(data_out);

    end block;


    ------------------------------------------------------------------------------
    resync_counter_narrow_no_output_register_block : block
      constant resync_idx : natural := 1;
      signal data_in, data_out : u_unsigned(2 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        -- If changed to +2, simulation should crash on assert false.
        data_in <= data_in + 1;
      end process;


      ------------------------------------------------------------------------------
      resync_counter_inst : entity resync.resync_counter
        generic map (
          width => data_in'length,
          pipeline_output => false
        )
        port map (
          clk_in => clk_s_hp0,
          counter_in => data_in,
          --
          clk_out => clk_ext,
          counter_out => data_out
        );

      ext_regs_up.resync(resync_idx).data(data_out'range) <= std_ulogic_vector(data_out);

    end block;


    ------------------------------------------------------------------------------
    resync_counter_wide_with_output_register_block : block
      constant resync_idx : natural := 2;
      signal data_in, data_out : u_unsigned(16 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        -- If changed to +2, simulation should crash on assert false.
        data_in <= data_in + 1;
      end process;


      ------------------------------------------------------------------------------
      resync_counter_inst : entity resync.resync_counter
        generic map (
          width => data_in'length,
          pipeline_output => true
        )
        port map (
          clk_in => clk_s_hp0,
          counter_in => data_in,
          --
          clk_out => clk_ext,
          counter_out => data_out
        );

      ext_regs_up.resync(resync_idx).data(data_out'range) <= std_ulogic_vector(data_out);

    end block;


    ------------------------------------------------------------------------------
    resync_counter_narrow_with_output_register_block : block
      constant resync_idx : natural := 3;
      signal data_in, data_out : u_unsigned(2 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        -- If changed to +2, simulation should crash on assert false.
        data_in <= data_in + 1;
      end process;


      ------------------------------------------------------------------------------
      resync_counter_inst : entity resync.resync_counter
        generic map (
          width => data_in'length,
          pipeline_output => true
        )
        port map (
          clk_in => clk_s_hp0,
          counter_in => data_in,
          --
          clk_out => clk_ext,
          counter_out => data_out
        );

      ext_regs_up.resync(resync_idx).data(data_out'range) <= std_ulogic_vector(data_out);

    end block;


    ------------------------------------------------------------------------------
    resync_cycles_wide_block : block
      constant resync_idx : natural := 4;
      signal data_in, data_out : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      resync_cycles_inst : entity resync.resync_cycles
        generic map (
          counter_width => 16
        )
        port map (
          clk_in => clk_s_hp0,
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(0);
      ext_regs_up.resync(resync_idx).data(0) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_cycles_narrow_block : block
      constant resync_idx : natural := 5;
      signal data_in, data_out : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      resync_cycles_inst : entity resync.resync_cycles
        generic map (
          counter_width => 2
        )
        port map (
          clk_in => clk_s_hp0,
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(0);
      ext_regs_up.resync(resync_idx).data(0) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_level_on_signal_block : block
      constant resync_idx : natural := 6;
      signal data_in, data_out, sample_value : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      resync_level_on_signal_inst : entity resync.resync_level_on_signal
        port map (
          data_in => data_in,
          --
          clk_out => clk_ext,
          sample_value => sample_value,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(0);

      sample_value <= ext_regs_down.resync(resync_idx).data(0);
      ext_regs_up.resync(resync_idx).data(0) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_level_with_clk_in_block : block
      constant resync_idx : natural := 7;
      signal data_in, data_out : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      resync_level_inst : entity resync.resync_level
        generic map (
          enable_input_register => false
        )
        port map (
          clk_in => clk_s_hp0,
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(0);
      ext_regs_up.resync(resync_idx).data(0) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_level_with_clk_in_and_input_register_block : block
      constant resync_idx : natural := 8;
      signal data_in, data_out : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      resync_level_inst : entity resync.resync_level
        generic map (
          enable_input_register => true
        )
        port map (
          clk_in => clk_s_hp0,
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(0);
      ext_regs_up.resync(resync_idx).data(0) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_level_without_clk_in_block : block
      constant resync_idx : natural := 9;
      signal data_in, data_out : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      resync_level_inst : entity resync.resync_level
        generic map (
          enable_input_register => false
        )
        port map (
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(0);
      ext_regs_up.resync(resync_idx).data(0) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_pulse_with_feedback_block : block
      constant resync_idx : natural := 10;
      signal data_in, data_out : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      resync_pulse_inst : entity resync.resync_pulse
        generic map (
          enable_feedback => true
        )
        port map (
          clk_in => clk_s_hp0,
          pulse_in => data_in,
          --
          clk_out => clk_ext,
          pulse_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(0);
      ext_regs_up.resync(resync_idx).data(0) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_pulse_without_feedback_block : block
      constant resync_idx : natural := 11;
      signal data_in, data_out : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      resync_pulse_inst : entity resync.resync_pulse
        generic map (
          enable_feedback => false
        )
        port map (
          clk_in => clk_s_hp0,
          pulse_in => data_in,
          --
          clk_out => clk_ext,
          pulse_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(0);
      ext_regs_up.resync(resync_idx).data(0) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_handshake_wide_block : block
      constant resync_idx : natural := 12;
      signal input_ready, input_valid, result_ready, result_valid : std_ulogic := '0';
      signal input_data, result_data : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      resync_slv_handshake_inst : entity resync.resync_slv_handshake
        generic map (
          data_width => input_data'length
        )
        port map (
          input_clk => clk_s_hp0,
          input_ready => input_ready,
          input_valid => input_valid,
          input_data => input_data,
          --
          result_clk => clk_ext,
          result_ready => result_ready,
          result_valid => result_valid,
          result_data => result_data
        );

      hp0_regs_up.resync(resync_idx).data(31) <= input_ready;
      input_valid <= hp0_regs_down.resync(resync_idx).data(31);
      input_data <= hp0_regs_down.resync(resync_idx).data(input_data'range);

      result_ready <= ext_regs_down.resync(resync_idx).data(31);
      ext_regs_up.resync(resync_idx).data(31) <= result_valid;
      ext_regs_up.resync(resync_idx).data(result_data'range) <= result_data;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_handshake_narrow_block : block
      constant resync_idx : natural := 13;
      signal input_ready, input_valid, result_ready, result_valid : std_ulogic := '0';
      signal input_data, result_data : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      resync_slv_handshake_inst : entity resync.resync_slv_handshake
        generic map (
          data_width => input_data'length
        )
        port map (
          input_clk => clk_s_hp0,
          input_ready => input_ready,
          input_valid => input_valid,
          input_data => input_data,
          --
          result_clk => clk_ext,
          result_ready => result_ready,
          result_valid => result_valid,
          result_data => result_data
        );

      hp0_regs_up.resync(resync_idx).data(31) <= input_ready;
      input_valid <= hp0_regs_down.resync(resync_idx).data(31);
      input_data <= hp0_regs_down.resync(resync_idx).data(input_data'range);

      result_ready <= ext_regs_down.resync(resync_idx).data(31);
      ext_regs_up.resync(resync_idx).data(31) <= result_valid;
      ext_regs_up.resync(resync_idx).data(result_data'range) <= result_data;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_coherent_wide_block : block
      constant resync_idx : natural := 14;
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      resync_slv_level_coherent_inst : entity resync.resync_slv_level_coherent
        generic map (
          width => data_in'length
        )
        port map (
          clk_in => clk_s_hp0,
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(data_in'range);
      ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_coherent_narrow_block : block
      constant resync_idx : natural := 15;
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      resync_slv_level_coherent_inst : entity resync.resync_slv_level_coherent
        generic map (
          width => data_in'length
        )
        port map (
          clk_in => clk_s_hp0,
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(data_in'range);
      ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_on_signal_wide_block : block
      constant resync_idx : natural := 16;
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
      signal sample_value : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      resync_slv_level_on_signal_inst : entity resync.resync_slv_level_on_signal
        generic map (
          width => data_in'length
        )
        port map (
          data_in => data_in,
          --
          clk_out => clk_ext,
          sample_value => sample_value,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(data_in'range);

      sample_value <= ext_regs_down.resync(resync_idx).data(0);
      ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_on_signal_narrow_block : block
      constant resync_idx : natural := 17;
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
      signal sample_value : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      resync_slv_level_on_signal_inst : entity resync.resync_slv_level_on_signal
        generic map (
          width => data_in'length
        )
        port map (
          data_in => data_in,
          --
          clk_out => clk_ext,
          sample_value => sample_value,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(data_in'range);

      sample_value <= ext_regs_down.resync(resync_idx).data(0);
      ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_without_clk_in_wide_block : block
      constant resync_idx : natural := 18;
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      resync_slv_level_inst : entity resync.resync_slv_level
        generic map (
          width => data_in'length,
          enable_input_register => false
        )
        port map (
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(data_in'range);
      ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_without_clk_in_narrow_block : block
      constant resync_idx : natural := 19;
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      resync_slv_level_inst : entity resync.resync_slv_level
        generic map (
          width => data_in'length,
          enable_input_register => false
        )
        port map (
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(data_in'range);
      ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_with_clk_in_wide_block : block
      constant resync_idx : natural := 20;
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      resync_slv_level_inst : entity resync.resync_slv_level
        generic map (
          width => data_in'length,
          enable_input_register => false
        )
        port map (
          clk_in => clk_s_hp0,
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(data_in'range);
      ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_with_clk_in_narrow_block : block
      constant resync_idx : natural := 21;
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      resync_slv_level_inst : entity resync.resync_slv_level
        generic map (
          width => data_in'length,
          enable_input_register => false
        )
        port map (
          clk_in => clk_s_hp0,
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(data_in'range);
      ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_with_input_register_wide_block : block
      constant resync_idx : natural := 22;
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      resync_slv_level_inst : entity resync.resync_slv_level
        generic map (
          width => data_in'length,
          enable_input_register => true
        )
        port map (
          clk_in => clk_s_hp0,
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(data_in'range);
      ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_with_input_register_narrow_block : block
      constant resync_idx : natural := 23;
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      resync_slv_level_inst : entity resync.resync_slv_level
        generic map (
          width => data_in'length,
          enable_input_register => true
        )
        port map (
          clk_in => clk_s_hp0,
          data_in => data_in,
          --
          clk_out => clk_ext,
          data_out => data_out
        );

      data_in <= hp0_regs_down.resync(resync_idx).data(data_in'range);
      ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    asynchronous_fifo_wide_deep_block : block
      constant resync_idx : natural := 24;
      signal write_ready, write_valid, read_ready, read_valid : std_ulogic := '0';
      signal write_data, read_data : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      deep_asynchronous_fifo_inst : entity fifo.asynchronous_fifo
        generic map (
          width => write_data'length,
          -- Suitable for BRAM.
          depth => 1024
        )
        port map (
          clk_write => clk_s_hp0,
          write_ready => write_ready,
          write_valid => write_valid,
          write_data => write_data,
          --
          clk_read => clk_ext,
          read_ready => read_ready,
          read_valid => read_valid,
          read_data => read_data
        );

      hp0_regs_up.resync(resync_idx).data(31) <= write_ready;
      write_valid <= hp0_regs_down.resync(resync_idx).data(31);
      write_data <= hp0_regs_down.resync(resync_idx).data(write_data'range);

      read_ready <= ext_regs_down.resync(resync_idx).data(31);
      ext_regs_up.resync(resync_idx).data(31) <= read_valid;
      ext_regs_up.resync(resync_idx).data(read_data'range) <= read_data;

    end block;


    ------------------------------------------------------------------------------
    asynchronous_fifo_wide_shallow_block : block
      constant resync_idx : natural := 25;
      signal write_ready, write_valid, read_ready, read_valid : std_ulogic := '0';
      signal write_data, read_data : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      deep_asynchronous_fifo_inst : entity fifo.asynchronous_fifo
        generic map (
          width => write_data'length,
          -- Suitable for LUTRAM.
          depth => 16
        )
        port map (
          clk_write => clk_s_hp0,
          write_ready => write_ready,
          write_valid => write_valid,
          write_data => write_data,
          --
          clk_read => clk_ext,
          read_ready => read_ready,
          read_valid => read_valid,
          read_data => read_data
        );

      hp0_regs_up.resync(resync_idx).data(31) <= write_ready;
      write_valid <= hp0_regs_down.resync(resync_idx).data(31);
      write_data <= hp0_regs_down.resync(resync_idx).data(write_data'range);

      read_ready <= ext_regs_down.resync(resync_idx).data(31);
      ext_regs_up.resync(resync_idx).data(31) <= read_valid;
      ext_regs_up.resync(resync_idx).data(read_data'range) <= read_data;

    end block;


    ------------------------------------------------------------------------------
    asynchronous_fifo_narrow_deep_block : block
      constant resync_idx : natural := 26;
      signal write_ready, write_valid, read_ready, read_valid : std_ulogic := '0';
      signal write_data, read_data : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      deep_asynchronous_fifo_inst : entity fifo.asynchronous_fifo
        generic map (
          width => write_data'length,
          -- Suitable for BRAM.
          depth => 1024
        )
        port map (
          clk_write => clk_s_hp0,
          write_ready => write_ready,
          write_valid => write_valid,
          write_data => write_data,
          --
          clk_read => clk_ext,
          read_ready => read_ready,
          read_valid => read_valid,
          read_data => read_data
        );

      hp0_regs_up.resync(resync_idx).data(31) <= write_ready;
      write_valid <= hp0_regs_down.resync(resync_idx).data(31);
      write_data <= hp0_regs_down.resync(resync_idx).data(write_data'range);

      read_ready <= ext_regs_down.resync(resync_idx).data(31);
      ext_regs_up.resync(resync_idx).data(31) <= read_valid;
      ext_regs_up.resync(resync_idx).data(read_data'range) <= read_data;

    end block;


    ------------------------------------------------------------------------------
    asynchronous_fifo_narrow_shallow_block : block
      constant resync_idx : natural := 27;
      signal write_ready, write_valid, read_ready, read_valid : std_ulogic := '0';
      signal write_data, read_data : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
    begin

      ------------------------------------------------------------------------------
      deep_asynchronous_fifo_inst : entity fifo.asynchronous_fifo
        generic map (
          width => write_data'length,
          -- Suitable for LUTRAM.
          depth => 16
        )
        port map (
          clk_write => clk_s_hp0,
          write_ready => write_ready,
          write_valid => write_valid,
          write_data => write_data,
          --
          clk_read => clk_ext,
          read_ready => read_ready,
          read_valid => read_valid,
          read_data => read_data
        );

      hp0_regs_up.resync(resync_idx).data(31) <= write_ready;
      write_valid <= hp0_regs_down.resync(resync_idx).data(31);
      write_data <= hp0_regs_down.resync(resync_idx).data(write_data'range);

      read_ready <= ext_regs_down.resync(resync_idx).data(31);
      ext_regs_up.resync(resync_idx).data(31) <= read_valid;
      ext_regs_up.resync(resync_idx).data(read_data'range) <= read_data;

    end block;

  end block;


  ------------------------------------------------------------------------------
  -- Instantiate protocol checker to show that it is indeed possible to
  -- synthesize code with this instance.
  axi_stream_protocol_checker_inst : entity common.axi_stream_protocol_checker
    generic map (
      data_width => s_hp0_m2s.write.w.data'length,
      logger_name_suffix => " - artyz7_top"
    )
    port map (
      clk => clk_s_hp0,
      --
      ready => s_hp0_s2m.write.w.ready,
      valid => s_hp0_m2s.write.w.valid,
      last => s_hp0_m2s.write.w.last,
      data => s_hp0_m2s.write.w.data,
      strobe => s_hp0_m2s.write.w.strb
    );

end architecture;
