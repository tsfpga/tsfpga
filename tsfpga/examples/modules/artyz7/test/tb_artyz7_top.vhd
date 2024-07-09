-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library osvvm;
use osvvm.RandomPkg.RandomPType;

library vunit_lib;
use vunit_lib.com_pkg.net;
use vunit_lib.memory_pkg.check_expected_was_written;
use vunit_lib.run_pkg.all;

library ddr_buffer;
use ddr_buffer.ddr_buffer_register_check_pkg.all;
use ddr_buffer.ddr_buffer_regs_pkg.all;
use ddr_buffer.ddr_buffer_sim_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.reg_t;
use reg_file.reg_operations_pkg.all;

use work.artyz7_top_pkg.all;
use work.block_design_mock_pkg.all;
use work.block_design_pkg.all;


entity tb_artyz7_top is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_artyz7_top is

  signal ext_clk : std_ulogic := '0';

begin

  test_runner_watchdog(runner, 200 us);
  ext_clk <= not ext_clk after 8 ns;


  ------------------------------------------------------------------------------
  main : process
    constant beef : reg_t := x"beef_beef";
    constant dead : reg_t := x"dead_dead";

    variable rnd : RandomPType;
  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    if run("test_register_read_write") then
      write_reg(net, 0, beef, base_address => regs_base_addresses(resync_ext_regs_idx));
      check_reg_equal(net, 0, beef, base_address => regs_base_addresses(resync_ext_regs_idx));

      write_reg(net, 0, dead, base_address => regs_base_addresses(resync_pl_regs_idx));
      check_reg_equal(net, 0, dead, base_address => regs_base_addresses(resync_pl_regs_idx));

      check_reg_equal(net, 0, beef, base_address => regs_base_addresses(resync_ext_regs_idx));

    elsif run("test_ddr_buffer") then
      run_ddr_buffer_test(
        net=>net,
        memory=>axi_memory,
        rnd=>rnd,
        regs_base_address=>regs_base_addresses(ddr_buffer_regs_idx)
      );
      check_ddr_buffer_status_counter_equal(
        net=>net,
        expected=>ddr_buffer_base_addresses_array_length,
        base_address=>regs_base_addresses(ddr_buffer_regs_idx)
      );

    end if;

    check_expected_was_written(axi_memory);

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.artyz7_top
    generic map (
      is_in_simulation => true
    )
    port map (
      enable_led => (others => '1'),
      ext_clk => ext_clk
    );

end architecture;
