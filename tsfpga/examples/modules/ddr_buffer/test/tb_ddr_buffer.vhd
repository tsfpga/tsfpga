-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library osvvm;
use osvvm.RandomPkg.all;

library vunit_lib;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;

library axi;
use axi.axi_pkg.all;
use axi.axi_lite_pkg.all;

library bfm;

library reg_file;
use reg_file.reg_file_pkg.all;
use reg_file.reg_operations_pkg.all;

use work.ddr_buffer_regs_pkg.all;
use work.ddr_buffer_sim_pkg.all;


entity tb_ddr_buffer is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_ddr_buffer is

  signal clk : std_ulogic := '0';
  signal axi_read_m2s : axi_read_m2s_t := axi_read_m2s_init;
  signal axi_read_s2m : axi_read_s2m_t := axi_read_s2m_init;

  signal axi_write_m2s : axi_write_m2s_t := axi_write_m2s_init;
  signal axi_write_s2m : axi_write_s2m_t := axi_write_s2m_init;

  signal regs_m2s : axi_lite_m2s_t := axi_lite_m2s_init;
  signal regs_s2m : axi_lite_s2m_t := axi_lite_s2m_init;

  constant axi_width : integer := 64;
  constant burst_length : integer := 16;
  constant burst_size_bytes : integer := burst_length * axi_width / 8;

  constant memory : memory_t := new_memory;
  constant axi_read_slave, axi_write_slave : axi_slave_t := new_axi_slave(
    address_fifo_depth => 1,
    memory => memory
  );

begin

  test_runner_watchdog(runner, 1 ms);
  clk <= not clk after 10 ns;


  ------------------------------------------------------------------------------
  main : process
    variable rnd : RandomPType;

    procedure check_counter(expected : natural) is
      variable reg_value : reg_t := (others => '0');
    begin
      read_reg(net, ddr_buffer_status, reg_value);
      check_equal(
        unsigned(reg_value(ddr_buffer_status_counter)),
        expected
      );
    end procedure;

  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    if run("test_ddr_buffer") then
      check_counter(0);

      run_ddr_buffer_test(net, memory, rnd);
      check_counter(ddr_buffer_addrs_array_length);

      run_ddr_buffer_test(net, memory, rnd);
      check_counter(2 * ddr_buffer_addrs_array_length);

    elsif run("test_version") then
      check_reg_equal(net, ddr_buffer_version, ddr_buffer_constant_version);

    end if;

    check_expected_was_written(memory);
    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  axi_lite_master_inst : entity bfm.axi_lite_master
    generic map (
      bus_handle => regs_bus_master
    )
    port map (
      clk => clk,

      axi_lite_m2s => regs_m2s,
      axi_lite_s2m => regs_s2m
    );


  ------------------------------------------------------------------------------
  axi_slave_inst : entity bfm.axi_slave
    generic map (
      axi_read_slave => axi_read_slave,
      axi_write_slave => axi_write_slave,
      data_width => axi_width,
      id_width => 0
    )
    port map (
      clk => clk,

      axi_read_m2s => axi_read_m2s,
      axi_read_s2m => axi_read_s2m,

      axi_write_m2s => axi_write_m2s,
      axi_write_s2m => axi_write_s2m
    );


  ------------------------------------------------------------------------------
  dut : entity work.ddr_buffer_top
    port map (
      clk => clk,

      axi_read_m2s => axi_read_m2s,
      axi_read_s2m => axi_read_s2m,

      axi_write_m2s => axi_write_m2s,
      axi_write_s2m => axi_write_s2m,

      regs_m2s => regs_m2s,
      regs_s2m => regs_s2m
    );

end architecture;
