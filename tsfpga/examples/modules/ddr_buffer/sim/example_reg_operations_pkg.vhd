-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

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
  -- register locations, defined below as well as in tsfpga.examples.example_env.py.

  constant config_reg : integer := 0;
  constant command_reg : integer := 1;
  constant status_reg : integer := 2;
  constant irq_status_reg : integer := 3;
  constant irq_mask_reg : integer := 4;

  procedure write_command(
    signal net : inout network_t;
    bit_index : in natural;
    base_address : in addr_t := (others => '0')
  );

  procedure wait_for_status_bit(
    signal net : inout network_t;
    bit_index : in natural;
    base_address : in addr_t := (others => '0')
  );

end;

package body example_reg_operations_pkg is

  procedure write_command(
    signal net : inout network_t;
    bit_index : in natural;
    base_address : in addr_t := (others => '0')
  ) is
  begin
    -- Command is a pulse-type register, so we do not need to do a read-modify-write.
    write_reg_bit(
      net=>net,
      reg_index=>command_reg,
      bit_index=>bit_index,
      value=>'1',
      base_address=>base_address
    );
  end procedure;

  procedure wait_for_status_bit(
    signal net : inout network_t;
    bit_index : in natural;
    base_address : in addr_t := (others => '0')
  ) is
  begin
    -- Wait until the indicated status bit is high. The other bits are ignored.

    wait_until_reg_equals_bit(
      net=>net,
      reg_index=>status_reg,
      bit_index=>bit_index,
      value=>'1',
      base_address=>base_address
    );
  end procedure;

end;
