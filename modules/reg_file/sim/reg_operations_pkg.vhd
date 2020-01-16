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


package reg_operations_pkg is

  -- Default bus handle that can be used to simplify calls.
  constant regs_bus_master : bus_master_t := new_bus(
    data_length => 32, address_length => 32, logger => get_logger("regs_bus_master"));

  -- Some common register operations. Some, e.g. write_command, rely on using the standard
  -- register locations definded below as well as in registers.py.

  constant config_reg : integer := 0;
  constant command_reg : integer := 1;
  constant status_reg : integer := 2;
  constant irq_status_reg : integer := 3;
  constant irq_mask_reg : integer := 4;

  procedure read_reg(
    signal net : inout network_t;
    reg_index : in integer;
    value : out reg_t;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

  procedure read_reg(
    signal net : inout network_t;
    reg_index : in integer;
    value : out integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

  procedure check_reg_equal(
    signal net : inout network_t;
    reg_index : in integer;
    expected : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

  procedure check_reg_equal(
    signal net : inout network_t;
    reg_index : in integer;
    expected : in reg_t;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

  procedure write_reg(
    signal net : inout network_t;
    reg_index : in integer;
    value : in reg_t;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

  procedure write_reg(
    signal net : inout network_t;
    reg_index : in integer;
    value : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

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

package body reg_operations_pkg is

  procedure read_reg(
    signal net : inout network_t;
    reg_index : in integer;
    value : out reg_t;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
    variable address : addr_t;
  begin
    address := base_address or std_logic_vector(to_unsigned(4 * reg_index, address'length));
    read_bus(net, bus_handle, address, value);
  end procedure;

  procedure read_reg(
    signal net : inout network_t;
    reg_index : in integer;
    value : out integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
    variable slv_value : reg_t;
  begin
    read_reg(net, reg_index, slv_value, base_address, bus_handle);
    value := to_integer(unsigned(slv_value));
  end procedure;

  procedure check_reg_equal(
    signal net : inout network_t;
    reg_index : in integer;
    expected : in reg_t;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
    variable got : reg_t;
  begin
    read_reg(net, reg_index, got, base_address, bus_handle);
    check_equal(got, expected, "base_address: " & to_string(base_address) & " reg_index: " & to_string(reg_index));
  end procedure;

  procedure check_reg_equal(
    signal net : inout network_t;
    reg_index : in integer;
    expected : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
    variable got : integer;
  begin
    read_reg(net, reg_index, got, base_address, bus_handle);
    check_equal(got, expected, "base_address: " & to_string(base_address) & " reg_index: " & to_string(reg_index));
  end procedure;

  procedure write_reg(
    signal net : inout network_t;
    reg_index : in integer;
    value : in reg_t;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
    variable address : addr_t;
  begin
      address := base_address or std_logic_vector(to_unsigned(4 * reg_index, address'length));
      write_bus(net, bus_handle, address, value);
    end procedure;

  procedure write_reg(
    signal net : inout network_t;
    reg_index : in integer;
    value : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
  begin
    write_reg(net, reg_index, std_logic_vector(to_signed(value, 32)), base_address, bus_handle);
  end procedure;

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
