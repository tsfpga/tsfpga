-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Build with an instance of each of the available resync block.
-- To show that the constraints work and the build passes timing.
------------------------------------------------------------------------------

library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;

library fifo;

library resync;

use work.artyz7_register_record_pkg.all;


entity resync_test is
  port (
    ext_clk : in std_ulogic;
    ext_regs_down : in artyz7_regs_down_t;
    ext_regs_up : out artyz7_regs_up_t := artyz7_regs_up_init;
    --
    pl_clk : in std_ulogic;
    pl_regs_down : in artyz7_regs_down_t;
    pl_regs_up : out artyz7_regs_up_t := artyz7_regs_up_init;
    --
    pl_clk_div4 : in std_ulogic;
    pl_div4_regs_down : in artyz7_regs_down_t;
    pl_div4_regs_up : out artyz7_regs_up_t := artyz7_regs_up_init
  );
end entity;

architecture a of resync_test is
begin

  ------------------------------------------------------------------------------
  resync_counter_wide_no_output_register_block : block
    constant resync_idx : natural := 0;
    signal data_in, data_out : u_unsigned(16 - 1 downto 0) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    assign_input : process
    begin
      wait until rising_edge(pl_clk);

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
        clk_in => pl_clk,
        counter_in => data_in,
        --
        clk_out => ext_clk,
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
      wait until rising_edge(pl_clk);

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
        clk_in => pl_clk,
        counter_in => data_in,
        --
        clk_out => ext_clk,
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
      wait until rising_edge(pl_clk);

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
        clk_in => pl_clk,
        counter_in => data_in,
        --
        clk_out => ext_clk,
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
      wait until rising_edge(pl_clk);

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
        clk_in => pl_clk,
        counter_in => data_in,
        --
        clk_out => ext_clk,
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
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(0);
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
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(0);
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
        clk_out => ext_clk,
        sample_value => sample_value,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(0);

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
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(0);
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
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(0);
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
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(0);
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
        clk_in => pl_clk,
        pulse_in => data_in,
        --
        clk_out => ext_clk,
        pulse_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(0);
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
        clk_in => pl_clk,
        pulse_in => data_in,
        --
        clk_out => ext_clk,
        pulse_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(0);
    ext_regs_up.resync(resync_idx).data(0) <= data_out;

  end block;


  ------------------------------------------------------------------------------
  resync_twophase_handshake_wide_block : block
    constant resync_idx : natural := 12;
    signal input_ready, input_valid, result_ready, result_valid : std_ulogic := '0';
    signal input_data, result_data : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    resync_twophase_handshake_inst : entity resync.resync_twophase_handshake
      generic map (
        data_width => input_data'length
      )
      port map (
        input_clk => pl_clk,
        input_ready => input_ready,
        input_valid => input_valid,
        input_data => input_data,
        --
        result_clk => ext_clk,
        result_ready => result_ready,
        result_valid => result_valid,
        result_data => result_data
      );

    pl_regs_up.resync(resync_idx).data(31) <= input_ready;
    input_valid <= pl_regs_down.resync(resync_idx).data(31);
    input_data <= pl_regs_down.resync(resync_idx).data(input_data'range);

    result_ready <= ext_regs_down.resync(resync_idx).data(31);
    ext_regs_up.resync(resync_idx).data(31) <= result_valid;
    ext_regs_up.resync(resync_idx).data(result_data'range) <= result_data;

  end block;


  ------------------------------------------------------------------------------
  resync_twophase_handshake_narrow_block : block
    constant resync_idx : natural := 13;
    signal input_ready, input_valid, result_ready, result_valid : std_ulogic := '0';
    signal input_data, result_data : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    resync_twophase_handshake_inst : entity resync.resync_twophase_handshake
      generic map (
        data_width => input_data'length
      )
      port map (
        input_clk => pl_clk,
        input_ready => input_ready,
        input_valid => input_valid,
        input_data => input_data,
        --
        result_clk => ext_clk,
        result_ready => result_ready,
        result_valid => result_valid,
        result_data => result_data
      );

    pl_regs_up.resync(resync_idx).data(31) <= input_ready;
    input_valid <= pl_regs_down.resync(resync_idx).data(31);
    input_data <= pl_regs_down.resync(resync_idx).data(input_data'range);

    result_ready <= ext_regs_down.resync(resync_idx).data(31);
    ext_regs_up.resync(resync_idx).data(31) <= result_valid;
    ext_regs_up.resync(resync_idx).data(result_data'range) <= result_data;

  end block;


  ------------------------------------------------------------------------------
  resync_twophase_wide_block : block
    constant resync_idx : natural := 14;
    signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    resync_twophase_inst : entity resync.resync_twophase
      generic map (
        width => data_in'length
      )
      port map (
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);
    ext_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

  end block;


  ------------------------------------------------------------------------------
  resync_twophase_narrow_block : block
    constant resync_idx : natural := 15;
    signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    resync_twophase_inst : entity resync.resync_twophase
      generic map (
        width => data_in'length
      )
      port map (
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);
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
        clk_out => ext_clk,
        sample_value => sample_value,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);

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
        clk_out => ext_clk,
        sample_value => sample_value,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);

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
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);
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
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);
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
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);
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
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);
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
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);
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
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => ext_clk,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);
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
        clk_write => pl_clk,
        write_ready => write_ready,
        write_valid => write_valid,
        write_data => write_data,
        --
        clk_read => ext_clk,
        read_ready => read_ready,
        read_valid => read_valid,
        read_data => read_data
      );

    pl_regs_up.resync(resync_idx).data(31) <= write_ready;
    write_valid <= pl_regs_down.resync(resync_idx).data(31);
    write_data <= pl_regs_down.resync(resync_idx).data(write_data'range);

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
        clk_write => pl_clk,
        write_ready => write_ready,
        write_valid => write_valid,
        write_data => write_data,
        --
        clk_read => ext_clk,
        read_ready => read_ready,
        read_valid => read_valid,
        read_data => read_data
      );

    pl_regs_up.resync(resync_idx).data(31) <= write_ready;
    write_valid <= pl_regs_down.resync(resync_idx).data(31);
    write_data <= pl_regs_down.resync(resync_idx).data(write_data'range);

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
        clk_write => pl_clk,
        write_ready => write_ready,
        write_valid => write_valid,
        write_data => write_data,
        --
        clk_read => ext_clk,
        read_ready => read_ready,
        read_valid => read_valid,
        read_data => read_data
      );

    pl_regs_up.resync(resync_idx).data(31) <= write_ready;
    write_valid <= pl_regs_down.resync(resync_idx).data(31);
    write_data <= pl_regs_down.resync(resync_idx).data(write_data'range);

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
        clk_write => pl_clk,
        write_ready => write_ready,
        write_valid => write_valid,
        write_data => write_data,
        --
        clk_read => ext_clk,
        read_ready => read_ready,
        read_valid => read_valid,
        read_data => read_data
      );

    pl_regs_up.resync(resync_idx).data(31) <= write_ready;
    write_valid <= pl_regs_down.resync(resync_idx).data(31);
    write_data <= pl_regs_down.resync(resync_idx).data(write_data'range);

    read_ready <= ext_regs_down.resync(resync_idx).data(31);
    ext_regs_up.resync(resync_idx).data(31) <= read_valid;
    ext_regs_up.resync(resync_idx).data(read_data'range) <= read_data;

  end block;


  ------------------------------------------------------------------------------
  -- A crossing between to clock that are synchronous.
  -- Can just assign, without needing any constraints.
  synchronous_crossing_block : block
    constant resync_idx : natural := 28;
  begin

    pl_regs_up.resync(resync_idx).data <= pl_div4_regs_down.resync(resync_idx).data;

    pl_div4_regs_up.resync(resync_idx).data <= pl_regs_down.resync(resync_idx).data;

  end block;


  ------------------------------------------------------------------------------
  -- A crossing between to clock that are synchronous.
  -- Instantiate one of our CDC blocks, to show that everything works also when clocks are
  -- synchronous.
  synchronous_crossing_with_cdc_block : block
    constant resync_idx : natural := 29;
    signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
  begin

    ------------------------------------------------------------------------------
    resync_slv_level_inst : entity resync.resync_slv_level
      generic map (
        width => data_in'length,
        enable_input_register => true
      )
      port map (
        clk_in => pl_clk,
        data_in => data_in,
        --
        clk_out => pl_clk_div4,
        data_out => data_out
      );

    data_in <= pl_regs_down.resync(resync_idx).data(data_in'range);
    pl_div4_regs_up.resync(resync_idx).data(data_out'range) <= data_out;

  end block;

end architecture;
