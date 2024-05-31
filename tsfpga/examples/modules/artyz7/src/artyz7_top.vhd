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


entity artyz7_top is
  port (
    clk_ext : in std_ulogic;
    --# {{}}
    led : out std_ulogic_vector(0 to 3) := (others => '0');
    dummy_output : out std_ulogic_vector(23 - 1 downto 0) := (others => '0')
  );
end entity;

architecture a of artyz7_top is

  signal clk_m_gp0 : std_ulogic := '0';
  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

  signal clk_s_hp0 : std_ulogic := '0';
  signal s_hp0_m2s : axi_m2s_t := axi_m2s_init;
  signal s_hp0_s2m : axi_s2m_t := axi_s2m_init;

  signal regs_m2s : axi_lite_m2s_vec_t(regs_base_addresses'range) := (others => axi_lite_m2s_init);
  signal regs_s2m : axi_lite_s2m_vec_t(regs_base_addresses'range) := (others => axi_lite_s2m_init);

begin

  ------------------------------------------------------------------------------
  blink_0 : process
    variable count : u_unsigned(27 - 1 downto 0) := (others => '0');
  begin
    wait until rising_edge(clk_m_gp0);

    led(0) <= count(count'high);
    count := count + 1;
  end process;


  ------------------------------------------------------------------------------
  blink_1 : process
    variable count : u_unsigned(27 - 1 downto 0) := (others => '0');
  begin
    wait until rising_edge(clk_s_hp0);

    led(1) <= count(count'high);
    count := count + 1;
  end process;


  ------------------------------------------------------------------------------
  regs_block : block
    -- Set up some registers to be in same clock domain as AXI port,
    -- and some to be in another clock domain.
    constant clocks_are_the_same : boolean_vector(regs_base_addresses'range) :=
      (ddr_buffer_regs_idx => false, dummy_reg_slaves => true);
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
        clk_axi_lite_vec(ddr_buffer_regs_idx) => clk_s_hp0,
        clk_axi_lite_vec(dummy_reg_slaves) => (dummy_reg_slaves => '0'),
        axi_lite_m2s_vec => regs_m2s,
        axi_lite_s2m_vec => regs_s2m
      );


    ------------------------------------------------------------------------------
    register_maps : for slave in dummy_reg_slaves generate

      ------------------------------------------------------------------------------
      axi_lite_reg_file_inst : entity reg_file.axi_lite_reg_file
        generic map (
          regs => artyz7_reg_map,
          default_values => artyz7_regs_init
        )
        port map (
          clk => clk_m_gp0,
          --
          axi_lite_m2s => regs_m2s(slave),
          axi_lite_s2m => regs_s2m(slave)
        );

    end generate;

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
  -- Build with an instance of each of the available resync block. To show that the constraints work
  -- and the build passes timing.
  -- All resync should be from internal clock to clk_ext.
  resync_test_block : block

    signal resync_input, resync_output : std_ulogic_vector(dummy_output'range) := (others => '0');
    signal input_pulse, output_pulse : std_ulogic := '0';

  begin

    ------------------------------------------------------------------------------
    set_input : process
    begin
      wait until rising_edge(clk_s_hp0);

      -- Dummy bits for input.
      -- Do not use more than the 32 bits that are actually assigned by the register bus.
      -- Vivado will strip the logic since input will be '-'.
      resync_input <= regs_m2s(ddr_buffer_regs_idx).write.w.data(resync_input'range);
    end process;


    ------------------------------------------------------------------------------
    input_pulse_block : block
      signal shift_register : std_ulogic_vector(0 to 8 - 1) := (0 => '1', others => '0');
    begin

      ------------------------------------------------------------------------------
      rotate_register : process
      begin
        wait until rising_edge(clk_s_hp0);

        shift_register <= (
          shift_register(shift_register'right)
          & shift_register(shift_register'left to shift_register'right - 1)
        );
      end process;

      input_pulse <= shift_register(0);

    end block;


    ------------------------------------------------------------------------------
    assign_output : process
    begin
      wait until rising_edge(clk_ext);

      dummy_output <= resync_output;
    end process;


    ------------------------------------------------------------------------------
    output_pulse_block : block
      signal shift_register : std_ulogic_vector(0 to 8 - 1) := (0 => '1', others => '0');
    begin

      ------------------------------------------------------------------------------
      rotate_register : process
      begin
        wait until rising_edge(clk_ext);

        shift_register <= (
          shift_register(shift_register'right)
          & shift_register(shift_register'left to shift_register'right - 1)
        );
      end process;

      output_pulse <= shift_register(0);

    end block;


    ------------------------------------------------------------------------------
    resync_counter_wide_no_output_register_block : block
      signal data_in, data_out : u_unsigned(16 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
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

      resync_output(0) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_counter_narrow_no_output_register_block : block
      signal data_in, data_out : u_unsigned(2 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
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

      resync_output(1) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_counter_wide_with_output_register_block : block
      signal data_in, data_out : u_unsigned(16 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
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

      resync_output(2) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_counter_narrow_with_output_register_block : block
      signal data_in, data_out : u_unsigned(2 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
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

      resync_output(3) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_cycles_wide_block : block
      signal data_in, data_out : std_ulogic := '0';
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(0);
      end process;


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

      resync_output(4) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_cycles_narrow_block : block
      signal data_in, data_out : std_ulogic := '0';
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(0);
      end process;


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

      resync_output(5) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_level_on_signal_block : block
      signal data_in, data_out : std_ulogic := '0';
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(0);
      end process;


      ------------------------------------------------------------------------------
      resync_level_on_signal_inst : entity resync.resync_level_on_signal
        port map (
          data_in => data_in,
          --
          clk_out => clk_ext,
          sample_value => output_pulse,
          data_out => data_out
        );

      resync_output(6) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_level_with_clk_in_block : block
      signal data_in, data_out : std_ulogic := '0';
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(0);
      end process;


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

      resync_output(7) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_level_with_clk_in_and_input_register_block : block
      signal data_in, data_out : std_ulogic := '0';
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(0);
      end process;


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

      resync_output(8) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_level_without_clk_in_block : block
      signal data_in, data_out : std_ulogic := '0';
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(0);
      end process;


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

      resync_output(9) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_pulse_block : block
      signal data_in, data_out : std_ulogic := '0';
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= input_pulse;
      end process;


      ------------------------------------------------------------------------------
      resync_pulse_inst : entity resync.resync_pulse
        port map (
          clk_in => clk_s_hp0,
          pulse_in => data_in,
          --
          clk_out => clk_ext,
          pulse_out => data_out
        );

      resync_output(10) <= data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_coherent_wide_block : block
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


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

      resync_output(11) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_coherent_narrow_block : block
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


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

      resync_output(12) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_on_signal_wide_block : block
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


      ------------------------------------------------------------------------------
      resync_slv_level_on_signal_inst : entity resync.resync_slv_level_on_signal
        generic map (
          width => data_in'length
        )
        port map (
          data_in => data_in,
          --
          clk_out => clk_ext,
          sample_value => output_pulse,
          data_out => data_out
        );


      resync_output(13) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_on_signal_narrow_block : block
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


      ------------------------------------------------------------------------------
      resync_slv_level_on_signal_inst : entity resync.resync_slv_level_on_signal
        generic map (
          width => data_in'length
        )
        port map (
          data_in => data_in,
          --
          clk_out => clk_ext,
          sample_value => output_pulse,
          data_out => data_out
        );


      resync_output(14) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_without_clk_in_wide_block : block
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


      ------------------------------------------------------------------------------
      resync_slv_level_without_clk_in_inst : entity resync.resync_slv_level
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

      resync_output(15) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_without_clk_in_narrow_block : block
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


      ------------------------------------------------------------------------------
      resync_slv_level_without_clk_in_inst : entity resync.resync_slv_level
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

      resync_output(16) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_with_input_register_wide_block : block
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


      ------------------------------------------------------------------------------
      resync_slv_level_without_clk_in_inst : entity resync.resync_slv_level
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

      resync_output(17) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    resync_slv_level_with_input_register_narrow_block : block
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";
    begin

      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


      ------------------------------------------------------------------------------
      resync_slv_level_without_clk_in_inst : entity resync.resync_slv_level
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

      resync_output(18) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    asynchronous_fifo_wide_deep_block : block
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";

      signal write_ready, write_valid, read_ready, read_valid : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      assign_handshake_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        write_valid <= write_ready and input_pulse;
      end process;


      ------------------------------------------------------------------------------
      assign_handshake_output : process
      begin
        wait until rising_edge(clk_ext);

        read_ready <= read_valid and output_pulse;
      end process;


      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


      ------------------------------------------------------------------------------
      deep_asynchronous_fifo_inst : entity fifo.asynchronous_fifo
        generic map (
          width => data_in'length,
          -- Suitable for BRAM.
          depth => 1024
        )
        port map (
          clk_read => clk_ext,
          read_ready => read_ready,
          read_valid => read_valid,
          read_data => data_out,
          --
          clk_write => clk_s_hp0,
          write_ready => write_ready,
          write_valid => write_valid,
          write_data => data_in
        );

      resync_output(19) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    asynchronous_fifo_wide_shallow_block : block
      signal data_in, data_out : std_ulogic_vector(16 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";

      signal write_ready, write_valid, read_ready, read_valid : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      assign_handshake_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        write_valid <= write_ready and input_pulse;
      end process;


      ------------------------------------------------------------------------------
      assign_handshake_output : process
      begin
        wait until rising_edge(clk_ext);

        read_ready <= read_valid and output_pulse;
      end process;


      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


      ------------------------------------------------------------------------------
      deep_asynchronous_fifo_inst : entity fifo.asynchronous_fifo
        generic map (
          width => data_in'length,
          -- Suitable for LUTRAM.
          depth => 16
        )
        port map (
          clk_read => clk_ext,
          read_ready => read_ready,
          read_valid => read_valid,
          read_data => data_out,
          --
          clk_write => clk_s_hp0,
          write_ready => write_ready,
          write_valid => write_valid,
          write_data => data_in
        );

      resync_output(20) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    asynchronous_fifo_narrow_deep_block : block
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";

      signal write_ready, write_valid, read_ready, read_valid : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      assign_handshake_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        write_valid <= write_ready and input_pulse;
      end process;


      ------------------------------------------------------------------------------
      assign_handshake_output : process
      begin
        wait until rising_edge(clk_ext);

        read_ready <= read_valid and output_pulse;
      end process;


      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


      ------------------------------------------------------------------------------
      deep_asynchronous_fifo_inst : entity fifo.asynchronous_fifo
        generic map (
          width => data_in'length,
          -- Suitable for BRAM.
          depth => 1024
        )
        port map (
          clk_read => clk_ext,
          read_ready => read_ready,
          read_valid => read_valid,
          read_data => data_out,
          --
          clk_write => clk_s_hp0,
          write_ready => write_ready,
          write_valid => write_valid,
          write_data => data_in
        );

      resync_output(21) <= xor data_out;

    end block;


    ------------------------------------------------------------------------------
    asynchronous_fifo_narrow_shallow_block : block
      signal data_in, data_out : std_ulogic_vector(2 - 1 downto 0) := (others => '0');
      attribute dont_touch of data_in : signal is "true";

      signal write_ready, write_valid, read_ready, read_valid : std_ulogic := '0';
    begin

      ------------------------------------------------------------------------------
      assign_handshake_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        write_valid <= write_ready and input_pulse;
      end process;


      ------------------------------------------------------------------------------
      assign_handshake_output : process
      begin
        wait until rising_edge(clk_ext);

        read_ready <= read_valid and output_pulse;
      end process;


      ------------------------------------------------------------------------------
      assign_input : process
      begin
        wait until rising_edge(clk_s_hp0);

        data_in <= resync_input(data_in'range);
      end process;


      ------------------------------------------------------------------------------
      deep_asynchronous_fifo_inst : entity fifo.asynchronous_fifo
        generic map (
          width => data_in'length,
          -- Suitable for LUTRAM.
          depth => 16
        )
        port map (
          clk_read => clk_ext,
          read_ready => read_ready,
          read_valid => read_valid,
          read_data => data_out,
          --
          clk_write => clk_s_hp0,
          write_ready => write_ready,
          write_valid => write_valid,
          write_data => data_in
        );

      resync_output(22) <= xor data_out;

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
