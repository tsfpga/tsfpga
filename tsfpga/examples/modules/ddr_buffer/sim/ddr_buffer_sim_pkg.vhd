-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
use vunit_lib.random_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;

library osvvm;
use osvvm.RandomPkg.all;

library common;
use common.addr_pkg.all;

library reg_file;
use reg_file.reg_operations_pkg.all;

use work.ddr_buffer_regs_pkg.all;
use work.example_reg_operations_pkg.all;


package ddr_buffer_sim_pkg is

  procedure run_ddr_buffer_test(signal net : inout network_t;
                                memory : in memory_t;
                                rnd : inout RandomPType;
                                regs_base_address : in addr_t := (others => '0'));

end package;

package body ddr_buffer_sim_pkg is

  procedure run_ddr_buffer_test(
    signal net : inout network_t;
    memory : in memory_t;
    rnd : inout RandomPType;
    regs_base_address : in addr_t := (others => '0')
  ) is
    constant burst_length_bytes : integer :=
      ddr_buffer_constant_burst_length_beats * (ddr_buffer_constant_axi_data_width / 8);
    variable memory_data : integer_array_t := null_integer_array;
    variable buf : buffer_t;
  begin
    for current_addr_index in 0 to ddr_buffer_addrs_array_length - 1 loop
      random_integer_array(rnd, memory_data, width=>burst_length_bytes, bits_per_word=>8);

      buf := write_integer_array(memory, memory_data, "read data", permissions=>read_only);
      write_reg(
        net,
        ddr_buffer_addrs_read_addr(current_addr_index),
        base_address(buf),
        regs_base_address
      );

      buf := set_expected_integer_array(memory, memory_data, "write data", permissions=>write_only);
      write_reg(
        net,
        ddr_buffer_addrs_write_addr(current_addr_index),
        base_address(buf),
        regs_base_address
      );
    end loop;

    write_command(net, ddr_buffer_command_start, regs_base_address);
    wait_for_status_bit(net, ddr_buffer_status_idle, regs_base_address);

    check_expected_was_written(memory);
  end procedure;

end package body;
