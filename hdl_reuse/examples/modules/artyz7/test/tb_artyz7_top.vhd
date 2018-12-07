library ieee;
use ieee.std_logic_1164.all;

library osvvm;
use osvvm.RandomPkg.all;

library vunit_lib;
use vunit_lib.memory_utils_pkg.all;
use vunit_lib.random_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;

library ddr_buffer;
use ddr_buffer.ddr_buffer_regs_pkg.all;

library reg_file;
use reg_file.reg_operations_pkg.all;

use work.artyz7_top_pkg.all;
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
    constant beef : std_logic_vector(32 - 1 downto 0) := x"beef_beef";
    constant dead : std_logic_vector(32 - 1 downto 0) := x"dead_dead";
    constant all_zero : std_logic_vector(32 - 1 downto 0) := x"0000_0000";

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
      write_bus(net, regs_axi_master, reg_slaves(0).addr or x"43c0_0000", beef);
      check_bus(net, regs_axi_master, reg_slaves(0).addr or x"43c0_0000", beef);

      -- Write different value to same register in another register map.
      -- Should be in another clock domain to verify CDC.
      write_bus(net, regs_axi_master, reg_slaves(ddr_buffer_regs_idx).addr or x"43c0_0000", dead);
      check_bus(net, regs_axi_master, reg_slaves(ddr_buffer_regs_idx).addr or x"43c0_0000", dead);

      check_bus(net, regs_axi_master, reg_slaves(0).addr or x"43c0_0000", beef);

    elsif run("test_ddr_buffer") then
      random_integer_array(rnd, memory_data, width=>burst_size_bytes, bits_per_word=>8);

      buf := write_integer_array(axi_memory, memory_data, "read data", permissions=>read_only);
      write_reg(net, regs_axi_master, ddr_buffer_read_addr, base_address(buf), ddr_buffer_regs_base_addr);

      buf := set_expected_integer_array(axi_memory, memory_data, "write data", permissions=>write_only);
      write_reg(net, regs_axi_master, ddr_buffer_write_addr, base_address(buf), ddr_buffer_regs_base_addr);

      write_command(net, regs_axi_master, ddr_buffer_command_start, ddr_buffer_regs_base_addr);
      wait_for_status_bit(net, regs_axi_master, ddr_buffer_status_idle, ddr_buffer_regs_base_addr);

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
