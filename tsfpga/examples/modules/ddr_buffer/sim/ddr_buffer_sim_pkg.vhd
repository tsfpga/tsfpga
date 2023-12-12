-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
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

use work.ddr_buffer_register_read_write_pkg.all;
use work.ddr_buffer_register_wait_until_pkg.all;
use work.ddr_buffer_regs_pkg.all;


package ddr_buffer_sim_pkg is

  procedure run_ddr_buffer_test(
    signal net : inout network_t;
    memory : in memory_t;
    rnd : inout RandomPType;
    regs_base_address : in addr_t := (others => '0')
  );

end package;

package body ddr_buffer_sim_pkg is

  procedure run_ddr_buffer_test(
    signal net : inout network_t;
    memory : in memory_t;
    rnd : inout RandomPType;
    regs_base_address : in addr_t := (others => '0')
  ) is
    constant burst_length_bytes : positive := (
      ddr_buffer_constant_burst_length_beats * (ddr_buffer_constant_axi_data_width / 8)
    );
    variable memory_data : integer_array_t := null_integer_array;
    variable buf : buffer_t;
  begin
    for current_addr_index in 0 to ddr_buffer_base_addresses_array_length - 1 loop
      random_integer_array(rnd, memory_data, width=>burst_length_bytes, bits_per_word=>8);

      buf := write_integer_array(
        memory, memory_data, "read_data_" & to_string(current_addr_index), permissions=>read_only
      );
      write_ddr_buffer_base_addresses_read_value(
        net=>net,
        array_index=>current_addr_index,
        value=>base_address(buf),
        base_address=>regs_base_address
      );

      buf := set_expected_integer_array(
        memory, memory_data, "write_data_" & to_string(current_addr_index), permissions=>write_only
      );
      write_ddr_buffer_base_addresses_write_value(
        net=>net,
        array_index=>current_addr_index,
        value=>base_address(buf),
        base_address=>regs_base_address
      );
    end loop;

    write_ddr_buffer_command_start(net=>net, value=>'1', base_address=>regs_base_address);
    wait_until_ddr_buffer_status_idle_equals(net=>net, value=>'1', base_address=>regs_base_address);
  end procedure;

end package body;
