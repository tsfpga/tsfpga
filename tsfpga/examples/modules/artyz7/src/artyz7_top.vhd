-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;

library axi;
use axi.axi_pkg.all;
use axi.axi_lite_pkg.all;

library common;
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
    led : out std_ulogic_vector(0 to 3) := (others => '0');
    dummy_output : out std_ulogic_vector(22 - 1 downto 0) := (others => '0')
  );
end entity;

architecture a of artyz7_top is

  signal clk_m_gp0 : std_ulogic := '0';
  signal m_gp0_m2s : axi_m2s_t := axi_m2s_init;
  signal m_gp0_s2m : axi_s2m_t := axi_s2m_init;

  signal clk_s_hp0 : std_ulogic := '0';
  signal s_hp0_m2s : axi_m2s_t := axi_m2s_init;
  signal s_hp0_s2m : axi_s2m_t := axi_s2m_init;

  signal regs_m2s : axi_lite_m2s_vec_t(reg_slaves'range) := (others => axi_lite_m2s_init);
  signal regs_s2m : axi_lite_s2m_vec_t(reg_slaves'range) := (others => axi_lite_s2m_init);

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
    constant clocks_are_the_same : boolean_vector(reg_slaves'range) :=
      (ddr_buffer_regs_idx => false, dummy_reg_slaves => true);
  begin

    ------------------------------------------------------------------------------
    axi_to_regs_inst : entity axi.axi_to_axi_lite_vec
      generic map (
        axi_lite_slaves => reg_slaves,
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
  resync_test_block : block

    signal misc_dummy_input, dummy_output_m1 : std_ulogic_vector(dummy_output'range) :=
      (others => '0');

    -- Dummy signal in clk_ext domain
    signal sample_value : std_ulogic := '0';
  begin

    -- Some dummy logic that instantiates a lot of the resync blocks.
    -- All resync should be from internal clock to clk_ext.
    assign_output : process
    begin
      wait until rising_edge(clk_ext);
      dummy_output <= dummy_output_m1;
    end process;

    -- Dummy bits for input.
    -- Do not use more than the 32 bits that are actually assigned by the register bus.
    -- Vivado will strip the logic since input will be '-'.
    misc_dummy_input <= regs_m2s(ddr_buffer_regs_idx).write.w.data(misc_dummy_input'range);


    ------------------------------------------------------------------------------
    resync_counter_inst : entity resync.resync_counter
      generic map (
        width => 4
      )
      port map (
        clk_in => clk_s_hp0,
        counter_in => unsigned(misc_dummy_input(3 downto 0)),
        --
        clk_out => clk_ext,
        std_logic_vector(counter_out) => dummy_output_m1(3 downto 0)
      );


    ------------------------------------------------------------------------------
    resync_cycles_inst : entity resync.resync_cycles
      generic map (
        counter_width => 8
      )
      port map (
        clk_in => clk_s_hp0,
        data_in => misc_dummy_input(4),
        --
        clk_out => clk_ext,
        data_out => dummy_output_m1(4)
      );


    ------------------------------------------------------------------------------
    resync_level_on_signal_inst : entity resync.resync_level_on_signal
      port map (
        data_in => misc_dummy_input(5),
        --
        clk_out => clk_ext,
        sample_value => sample_value,
        data_out => dummy_output_m1(5)
      );


    ------------------------------------------------------------------------------
    resync_level_with_clk_in_inst : entity resync.resync_level
      generic map (
        enable_input_register => false
      )
      port map (
        clk_in => clk_s_hp0,
        data_in => misc_dummy_input(6),
        --
        clk_out => clk_ext,
        data_out => dummy_output_m1(6)
      );


    ------------------------------------------------------------------------------
    resync_level_with_clk_in_and_input_register_inst : entity resync.resync_level
      generic map (
        enable_input_register => true
      )
      port map (
        clk_in => clk_s_hp0,
        data_in => misc_dummy_input(7),
        --
        clk_out => clk_ext,
        data_out => dummy_output_m1(7)
      );


    ------------------------------------------------------------------------------
    resync_level_without_clk_in_inst : entity resync.resync_level
      generic map (
        enable_input_register => false
      )
      port map (
        data_in => misc_dummy_input(8),
        --
        clk_out => clk_ext,
        data_out => dummy_output_m1(8)
      );

    sample_value <= dummy_output(8);


    ------------------------------------------------------------------------------
    resync_slv_level_on_signal_inst : entity resync.resync_slv_level_on_signal
      generic map (
        width => 2
      )
      port map (
        data_in => misc_dummy_input(10 downto 9),
        --
        clk_out => clk_ext,
        sample_value => sample_value,
        data_out => dummy_output_m1(10 downto 9)
      );


    ------------------------------------------------------------------------------
    resync_slv_level_without_clk_in_inst : entity resync.resync_slv_level
      generic map (
        width => 2,
        enable_input_register => false
      )
      port map (
        data_in => misc_dummy_input(12 downto 11),
        --
        clk_out => clk_ext,
        data_out => dummy_output_m1(12 downto 11)
      );


    ------------------------------------------------------------------------------
    resync_slv_level_with_input_register_inst : entity resync.resync_slv_level
      generic map (
        width => 2,
        enable_input_register => true
      )
      port map (
        clk_in => clk_s_hp0,
        data_in => misc_dummy_input(14 downto 13),
        --
        clk_out => clk_ext,
        data_out => dummy_output_m1(14 downto 13)
      );


    ------------------------------------------------------------------------------
    resync_slv_level_coherent_inst : entity resync.resync_slv_level_coherent
      generic map (
        width => 2
      )
      port map (
        clk_in => clk_s_hp0,
        data_in => misc_dummy_input(16 downto 15),
        --
        clk_out => clk_ext,
        data_out => dummy_output_m1(16 downto 15)
      );


    ------------------------------------------------------------------------------
    asynchronous_fifo_block : block

      -- We need to use a somewhat wide word in order to get Vivado to pack data in BRAM.
      -- We do no want to use the same bits as some other resync, so for FIFO we use another
      -- dummy input word.
      alias fifo_dummy_input is regs_m2s(dummy_reg_slaves'low).write.w.data;
      signal deep_read_data, shallow_read_data : std_ulogic_vector(16 - 1 downto 0) :=
        (others => '0');
      signal fifo_write_valid, fifo_read_ready : std_ulogic := '0';

    begin

      fifo_write_valid <=
        regs_s2m(dummy_reg_slaves'low).write.w.ready
        and regs_m2s(dummy_reg_slaves'low).write.w.valid;

      dummy_output_m1(17) <= xor deep_read_data;
      dummy_output_m1(18) <= xor shallow_read_data;


      ------------------------------------------------------------------------------
      deep_asynchronous_fifo_inst : entity fifo.asynchronous_fifo
        generic map (
          width => deep_read_data'length,
          -- Depth is selected to create a BRAM
          depth => 1024
        )
        port map (
          clk_read => clk_ext,
          read_ready => fifo_read_ready,
          read_valid => open,
          read_data => deep_read_data,
          --
          clk_write => clk_m_gp0,
          write_ready => open,
          write_valid => fifo_write_valid,
          write_data => fifo_dummy_input(31 downto 16)
        );


      ------------------------------------------------------------------------------
      shallow_asynchronous_fifo_inst : entity fifo.asynchronous_fifo
        generic map (
          width => shallow_read_data'length,
          -- Depth is selected to create a LUTRAM
          depth => 16
        )
        port map (
          clk_read => clk_ext,
          read_ready => fifo_read_ready,
          read_valid => open,
          read_data => shallow_read_data,
          --
          clk_write => clk_m_gp0,
          write_ready => open,
          write_valid => fifo_write_valid,
          write_data => fifo_dummy_input(15 downto 0)
        );


      ------------------------------------------------------------------------------
      resync_pulse_inst : entity resync.resync_pulse
        port map (
          clk_in => clk_m_gp0,
          pulse_in => fifo_write_valid,
          --
          clk_out => clk_ext,
          pulse_out => fifo_read_ready
        );

    end block;

  end block;


  ------------------------------------------------------------------------------
  -- Instantiate protocol checker within a simulation guard. To show that it is indeed possible to
  -- synthesize code with this instance.
  protocol_checker_test_gen : if in_simulation generate

    ------------------------------------------------------------------------------
    axi_stream_protocol_checker_inst : entity common.axi_stream_protocol_checker
      generic map (
        data_width => m_gp0_data_width
      )
      port map (
        clk => clk_m_gp0,
        --
        ready => m_gp0_s2m.write.w.ready,
        valid => m_gp0_m2s.write.w.valid,
        last => m_gp0_m2s.write.w.last,
        data => m_gp0_m2s.write.w.data(m_gp0_data_width - 1 downto 0),
        strobe => m_gp0_m2s.write.w.strb(m_gp0_data_width / 8 - 1 downto 0)
      );

  end generate;

end architecture;
