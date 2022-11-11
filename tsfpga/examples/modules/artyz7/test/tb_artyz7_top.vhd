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

library osvvm;
use osvvm.RandomPkg.all;

library vunit_lib;
use vunit_lib.memory_utils_pkg.all;
use vunit_lib.random_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;

library common;
use common.addr_pkg.all;

library ddr_buffer;
use ddr_buffer.ddr_buffer_regs_pkg.all;
use ddr_buffer.ddr_buffer_sim_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.all;
use reg_file.reg_operations_pkg.all;

use work.artyz7_top_pkg.all;
use work.artyz7_regs_pkg.all;
use work.top_level_sim_pkg.all;


entity tb_artyz7_top is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_artyz7_top is

  signal clk_ext : std_ulogic := '0';

begin

  test_runner_watchdog(runner, 200 us);
  clk_ext <= not clk_ext after 8 ns;


  ------------------------------------------------------------------------------
  main : process

    constant beef : reg_t := x"beef_beef";
    constant dead : reg_t := x"dead_dead";
    variable reg_value : reg_t := (others => '0');

    constant axi_width : integer := 64;
    constant burst_length : integer := 16;
    constant burst_size_bytes : integer := burst_length * axi_width / 8;

    variable rnd : RandomPType;
    variable memory_data : integer_array_t := null_integer_array;
    variable buf : buffer_t;
  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    if run("test_register_read_write") then
      write_reg(net, 0, beef, base_address => reg_slaves(0).addr);
      check_reg_equal(net, 0, beef, base_address => reg_slaves(0).addr);

      -- Write different value to same register in another register map.
      -- Should be in another clock domain to verify CDC.
      write_reg(net, 0, dead, base_address => reg_slaves(ddr_buffer_regs_idx).addr);
      check_reg_equal(net, 0, dead, base_address => reg_slaves(ddr_buffer_regs_idx).addr);

      check_reg_equal(net, 0, beef, base_address => reg_slaves(0).addr);

    elsif run("test_ddr_buffer") then
      run_ddr_buffer_test(net, axi_memory, rnd, ddr_buffer_regs_base_addr);
      check_expected_was_written(axi_memory);

    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.artyz7_top
  port map (
    clk_ext => clk_ext
  );

end architecture;
