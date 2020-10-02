-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;
context vunit_lib.vc_context;

library common;
use common.addr_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.all;
use reg_file.reg_operations_pkg.all;


package example_reg_operations_pkg is

  -- These convenience functions for the example modules rely on using the standard
  -- register locations, definded below as well as in tsfpga_example_env.py.

  constant config_reg : integer := 0;
  constant command_reg : integer := 1;
  constant status_reg : integer := 2;
  constant irq_status_reg : integer := 3;
  constant irq_mask_reg : integer := 4;

  procedure write_command(
    signal net : inout network_t;
    bit : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

  procedure wait_for_any_status_bit(
    signal net : inout network_t;
    bits : in integer_vector;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

  procedure wait_for_status_bit(
    signal net : inout network_t;
    bit : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

end;

package body example_reg_operations_pkg is

  procedure write_command(
    signal net : inout network_t;
    bit : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
    variable register_value : reg_t := (others => '0');
  begin
    register_value(bit) := '1';
    write_reg(net, command_reg, register_value, base_address, bus_handle);
  end procedure;

  procedure wait_for_any_status_bit(
    signal net : inout network_t;
    bits : in integer_vector;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
    variable read_value : reg_t;
  begin
    -- Returns when any of the specified bits are asserted

    read_loop : while true loop
      read_reg(net, status_reg, read_value, base_address, bus_handle);
      for bits_vector_loop_index in bits'range loop
        if read_value(bits(bits_vector_loop_index)) = '1' then
          exit read_loop;
        end if;
      end loop;
    end loop;
  end procedure;

  procedure wait_for_status_bit(
    signal net : inout network_t;
    bit : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
  begin
    wait_for_any_status_bit(net, (0 => bit), base_address, bus_handle);
  end procedure;

end;
