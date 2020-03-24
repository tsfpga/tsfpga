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

  procedure check_reg_equal_bits(
    signal net : inout network_t;
    reg_index : in integer;
    expected_bits : in integer_vector;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

  procedure check_reg_equal_bit(
    signal net : inout network_t;
    reg_index : in integer;
    expected_bit : in integer;
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

  procedure write_reg_bits(
    signal net : inout network_t;
    reg_index : in integer;
    bits : in integer_vector;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master);

  procedure write_reg_bit(
    signal net : inout network_t;
    reg_index : in integer;
    bit_index : in integer;
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

  procedure wait_until_reg_equals(
    signal net : inout network_t;
    reg_index : in integer;
    value : in reg_t;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master;
    timeout : delay_length := delay_length'high;
    message : string := "");

  procedure wait_until_reg_equals_bits(
    signal net : inout network_t;
    reg_index : in integer;
    bits : in integer_vector;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master;
    timeout : delay_length := delay_length'high;
    message : string := "");

  procedure wait_until_reg_equals_bit(
    signal net : inout network_t;
    reg_index : in integer;
    bit : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master;
    timeout : delay_length := delay_length'high;
    message : string := "");

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

  procedure check_reg_equal_bits(
    signal net : inout network_t;
    reg_index : in integer;
    expected_bits : in integer_vector;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
    variable expected : reg_t := (others => '0');
  begin
    -- Check that reg has value with only the bits in "expected_bits" set.
    for vec_index in expected_bits'range loop
      expected(expected_bits(vec_index)) := '1';
    end loop;
    check_reg_equal(net, reg_index, expected, base_address, bus_handle);
  end procedure;

  procedure check_reg_equal_bit(
    signal net : inout network_t;
    reg_index : in integer;
    expected_bit : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
  begin
    -- Check that reg has value with only the "expected_bit" bit set.
    check_reg_equal_bits(net, reg_index, (0 => expected_bit), base_address, bus_handle);
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

  procedure write_reg_bits(
    signal net : inout network_t;
    reg_index : in integer;
    bits : in integer_vector;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
    variable data : reg_t := (others => '0');
  begin
    -- Write with only the bits listed in "bits" asserted.
    for vec_index in bits'range loop
      data(bits(vec_index)) := '1';
    end loop;
    write_reg(net, reg_index, data, base_address, bus_handle);
  end procedure;

  procedure write_reg_bit(
    signal net : inout network_t;
    reg_index : in integer;
    bit_index : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master) is
  begin
    -- Write with only the bit "bit_index" asserted.
    write_reg_bits(net, reg_index, (0 => bit_index), base_address, bus_handle);
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

  procedure wait_until_reg_equals(
    signal net : inout network_t;
    reg_index : in integer;
    value : in reg_t;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master;
    timeout : delay_length := delay_length'high;
    message : string := "") is
    constant address : addr_t := base_address or std_logic_vector(to_unsigned(4 * reg_index, addr_t'length));
  begin
    wait_until_read_equals(net, bus_handle, address, value, timeout, message);
  end procedure;

  procedure wait_until_reg_equals_bits(
    signal net : inout network_t;
    reg_index : in integer;
    bits : in integer_vector;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master;
    timeout : delay_length := delay_length'high;
    message : string := "") is
    constant start_time : time := now;
    variable read_data : reg_t;
    variable test_ok : boolean;
  begin
    -- Wait until all the bits listed in "bits" are read as true.

    while now - start_time <= timeout loop
      read_reg(net, reg_index, read_data, base_address, bus_handle);

      test_ok := true;
      for vector_index in bits'range loop
        test_ok := test_ok and (read_data(bits(vector_index)) = '1');
      end loop;

      if test_ok then
        return;
      end if;
    end loop;

    assert false report "Timeout! " & message;
  end procedure;

  procedure wait_until_reg_equals_bit(
    signal net : inout network_t;
    reg_index : in integer;
    bit : in integer;
    base_address : in addr_t := (others => '0');
    bus_handle : in bus_master_t := regs_bus_master;
    timeout : delay_length := delay_length'high;
    message : string := "") is
  begin
    -- Wait until the bit in "bit" is read as true.
    wait_until_reg_equals_bits(net, reg_index, (0 => bit), base_address, bus_handle, timeout, message);
  end procedure;

end;
