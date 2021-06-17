-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
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

  signal clk_ext : std_logic := '0';

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

    elsif run("test_generated_register_adresses") then
      -- Default register
      check_equal(artyz7_config, 0);
      check_equal(artyz7_command, 1);
      check_equal(artyz7_status, 2);
      check_equal(artyz7_irq_status, 3);
      check_equal(artyz7_irq_mask, 4);

      -- Plain register from TOML
      check_equal(artyz7_plain_dummy_reg, 5);

      -- Register array from TOML
      check_equal(artyz7_dummy_regs_array_length, 3);

      check_equal(artyz7_dummy_regs_array_dummy_reg(0), 6);
      check_equal(artyz7_dummy_regs_second_array_dummy_reg(0), 7);
      check_equal(artyz7_dummy_regs_array_dummy_reg(1), 8);
      check_equal(artyz7_dummy_regs_second_array_dummy_reg(1), 9);
      check_equal(artyz7_dummy_regs_array_dummy_reg(2), 10);
      check_equal(artyz7_dummy_regs_second_array_dummy_reg(2), 11);

    elsif run("test_generated_register_modes") then
      -- Default register
      assert artyz7_reg_map(artyz7_config).reg_type = r_w;
      assert artyz7_reg_map(artyz7_command).reg_type = wpulse;
      assert artyz7_reg_map(artyz7_status).reg_type = r;
      assert artyz7_reg_map(artyz7_irq_status).reg_type = r_wpulse;
      assert artyz7_reg_map(artyz7_irq_mask).reg_type = r_w;

      -- Plain register from TOML
      assert artyz7_reg_map(artyz7_plain_dummy_reg).reg_type = r_w;

      -- Register array from TOML
      assert artyz7_reg_map(artyz7_dummy_regs_array_dummy_reg(0)).reg_type = r_w;
      assert artyz7_reg_map(artyz7_dummy_regs_second_array_dummy_reg(0)).reg_type = r;
      assert artyz7_reg_map(artyz7_dummy_regs_array_dummy_reg(1)).reg_type = r_w;
      assert artyz7_reg_map(artyz7_dummy_regs_second_array_dummy_reg(1)).reg_type = r;
      assert artyz7_reg_map(artyz7_dummy_regs_array_dummy_reg(2)).reg_type = r_w;
      assert artyz7_reg_map(artyz7_dummy_regs_second_array_dummy_reg(2)).reg_type = r;

    elsif run("test_generated_register_field_indexes") then
      -- Generated bit field indexes should match the order and widths in the TOML

      -- Fields in the plain register
      check_equal(artyz7_plain_dummy_reg_plain_bit_a, 0);
      check_equal(artyz7_plain_dummy_reg_plain_bit_b, 1);
      check_equal(artyz7_plain_dummy_reg_plain_bit_vector'low, 2);
      check_equal(artyz7_plain_dummy_reg_plain_bit_vector'high, 5);
      check_equal(artyz7_plain_dummy_reg_plain_bit_vector_width, 4);

      -- Fields in the register array register
      check_equal(artyz7_dummy_regs_array_dummy_reg_array_bit_a, 0);
      check_equal(artyz7_dummy_regs_array_dummy_reg_array_bit_b, 1);
      check_equal(artyz7_dummy_regs_array_dummy_reg_array_bit_vector'low, 2);
      check_equal(artyz7_dummy_regs_array_dummy_reg_array_bit_vector'high, 6);
      check_equal(artyz7_dummy_regs_array_dummy_reg_array_bit_vector_width, 5);

    elsif run("test_generated_register_default_values") then
      -- Test reading the default values set in the regs TOML

      read_reg(
        net,
        artyz7_plain_dummy_reg,
        reg_value,
        base_address => reg_slaves(0).addr
      );

      check_equal(reg_value(artyz7_plain_dummy_reg_plain_bit_a), '0');
      check_equal(reg_value(artyz7_plain_dummy_reg_plain_bit_b), '1');
      check_equal(unsigned(reg_value(artyz7_plain_dummy_reg_plain_bit_vector)), 3);

      for register_array_idx in 0 to 3 - 1 loop
        read_reg(
          net,
          artyz7_dummy_regs_array_dummy_reg(register_array_idx),
          reg_value,
          base_address => reg_slaves(0).addr
        );

        check_equal(reg_value(artyz7_dummy_regs_array_dummy_reg_array_bit_a), '1');
        check_equal(reg_value(artyz7_dummy_regs_array_dummy_reg_array_bit_b), '0');
        check_equal(unsigned(reg_value(artyz7_dummy_regs_array_dummy_reg_array_bit_vector)), 12);
      end loop;

    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.artyz7_top
  port map (
    clk_ext => clk_ext
  );

end architecture;
