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


package reg_operations_pkg is

  -- Some common register operations. Most of them rely on using the standard register locations
  -- definded below as well as in registers.py.

  constant config_reg : integer := 0;
  constant command_reg : integer := 1;
  constant status_reg : integer := 2;
  constant irq_status_reg : integer := 3;
  constant irq_mask_reg : integer := 4;

  procedure read_reg(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    reg_index : in integer;
    value : out reg_t;
    base_address : in addr_t := (others => '0'));

  procedure read_reg(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    reg_index : in integer;
    value : out integer;
    base_address : in addr_t := (others => '0'));

  procedure check_reg_equal(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    reg_index : in integer;
    expected : in integer;
    base_address : in addr_t := (others => '0'));

  procedure write_reg(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    reg_index : in integer;
    value : in reg_t;
    base_address : in addr_t := (others => '0'));

  procedure write_reg(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    reg_index : in integer;
    value : in integer;
    base_address : in addr_t := (others => '0'));

  procedure write_command(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    bit : in integer;
    base_address : in addr_t := (others => '0'));

  procedure wait_for_any_status_bit(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    bits : in integer_vector;
    base_address : in addr_t := (others => '0'));

  procedure wait_for_status_bit(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    bit : in integer;
    base_address : in addr_t := (others => '0'));

end;

package body reg_operations_pkg is

  procedure read_reg(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    reg_index : in integer;
    value : out reg_t;
    base_address : in addr_t := (others => '0')) is
    variable address : addr_t;
  begin
    address := base_address or std_logic_vector(to_unsigned(4 * reg_index, address'length));
    read_bus(net, bus_handle, address, value);
  end procedure;

  procedure read_reg(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    reg_index : in integer;
    value : out integer;
    base_address : in addr_t := (others => '0')) is
    variable slv_value : reg_t;
  begin
    read_reg(net, bus_handle, reg_index, slv_value);
    value := to_integer(unsigned(slv_value));
  end procedure;

  procedure check_reg_equal(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    reg_index : in integer;
    expected : in integer;
    base_address : in addr_t := (others => '0')) is
    variable got : integer;
  begin
    read_reg(net, bus_handle, reg_index, got);
    --check_equals(got, expected, "Reg index: " & to_string(reg_index));
    check_equal(got, expected);
  end procedure;

  procedure write_reg(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    reg_index : in integer;
    value : in reg_t;
    base_address : in addr_t := (others => '0')) is
    variable address : addr_t;
  begin
      address := base_address or std_logic_vector(to_unsigned(4 * reg_index, address'length));
      write_bus(net, bus_handle, address, value);
    end procedure;

  procedure write_reg(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    reg_index : in integer;
    value : in integer;
    base_address : in addr_t := (others => '0')) is
  begin
    write_reg(net, bus_handle, reg_index, std_logic_vector(to_signed(value, 32)), base_address);
  end procedure;

  procedure write_command(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    bit : in integer;
    base_address : in addr_t := (others => '0')) is
    variable register_value : reg_t := (others => '0');
  begin
    register_value(bit) := '1';
    write_reg(net, bus_handle, command_reg, register_value, base_address);
  end procedure;

  procedure wait_for_any_status_bit(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    bits : in integer_vector;
    base_address : in addr_t := (others => '0')) is
    variable read_value : reg_t;
  begin
    -- Returns when any of the specified bits are asserted

    read_loop : while true loop
      read_reg(net, bus_handle, status_reg, read_value, base_address);
      for bits_vector_loop_index in bits'range loop
        if read_value(bits(bits_vector_loop_index)) = '1' then
          exit read_loop;
        end if;
      end loop;
    end loop;
  end procedure;

  procedure wait_for_status_bit(
    signal net : inout network_t;
    bus_handle : in bus_master_t;
    bit : in integer;
    base_address : in addr_t := (others => '0')) is
  begin
    wait_for_any_status_bit(net, bus_handle, (0 => bit), base_address);
  end procedure;

end;
