-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library osvvm;
use osvvm.RandomPkg.all;

library vunit_lib;
use vunit_lib.memory_pkg.all;
use vunit_lib.memory_utils_pkg.all;
use vunit_lib.random_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;

library axi;
use axi.axi_pkg.all;
use axi.axil_pkg.all;

library bfm;

library reg_file;
use reg_file.reg_operations_pkg.all;

use work.ddr_buffer_regs_pkg.all;
use work.ddr_buffer_sim_pkg.all;


entity tb_ddr_buffer is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_ddr_buffer is

  signal clk_axi : std_logic := '0';
  signal axi_read_m2s : axi_read_m2s_t := axi_read_m2s_init;
  signal axi_read_s2m : axi_read_s2m_t := axi_read_s2m_init;

  signal axi_write_m2s : axi_write_m2s_t := axi_write_m2s_init;
  signal axi_write_s2m : axi_write_s2m_t := axi_write_s2m_init;

  signal regs_m2s : axil_m2s_t := axil_m2s_init;
  signal regs_s2m : axil_s2m_t := axil_s2m_init;

  constant axi_width : integer := 64;
  constant burst_length : integer := 16;
  constant burst_size_bytes : integer := burst_length * axi_width / 8;

  constant memory : memory_t := new_memory;
  constant axi_slave : axi_slave_t := new_axi_slave(address_fifo_depth => 1, memory => memory);

begin

  test_runner_watchdog(runner, 1 ms);
  clk_axi <= not clk_axi after 10 ns;


  ------------------------------------------------------------------------------
  main : process
    variable rnd : RandomPType;
    variable memory_data : integer_array_t := null_integer_array;
    variable buf : buffer_t;
  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    run_ddr_buffer_test(net, memory, rnd);

    check_expected_was_written(memory);
    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  axil_master_inst : entity bfm.axil_master
    generic map (
      bus_handle => regs_bus_master
    )
    port map (
      clk => clk_axi,

      axil_m2s => regs_m2s,
      axil_s2m => regs_s2m
    );


  ------------------------------------------------------------------------------
  axi_slave_inst : entity bfm.axi_slave
    generic map (
      axi_slave => axi_slave,
      data_width => axi_width
    )
    port map (
      clk => clk_axi,

      axi_read_m2s => axi_read_m2s,
      axi_read_s2m => axi_read_s2m,

      axi_write_m2s => axi_write_m2s,
      axi_write_s2m => axi_write_s2m
    );


  ------------------------------------------------------------------------------
  dut : entity work.ddr_buffer_top
    port map (
      clk_axi_read => clk_axi,
      axi_read_m2s => axi_read_m2s,
      axi_read_s2m => axi_read_s2m,

      clk_axi_write => clk_axi,
      axi_write_m2s => axi_write_m2s,
      axi_write_s2m => axi_write_s2m,

      clk_regs => clk_axi,
      regs_m2s => regs_m2s,
      regs_s2m => regs_s2m
    );

end architecture;
