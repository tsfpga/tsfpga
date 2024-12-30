-- -----------------------------------------------------------------------------
-- This file is automatically generated by hdl-registers version 6.2.1-dev2.
-- Code generator VhdlRegisterPackageGenerator version 1.0.0.
-- Generated 2024-12-30 14:53 from file regs_register_top_level.toml at commit a88ea51b9e82.
-- Register hash 5389169bfaee4103dfc57327d36576428cd8e774.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.fixed_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.all;


package register_top_level_regs_pkg is

  -- ---------------------------------------------------------------------------
  -- Values of register constants.
  constant register_top_level_constant_num_register_lists : integer := 15;

  -- ---------------------------------------------------------------------------
  -- The valid range of register indexes.
  subtype register_top_level_reg_range is natural range 0 to 24;

  -- Number of times the 'registers' register array is repeated.
  constant register_top_level_registers_array_length : natural := 20;
  -- Range for indexing 'registers' register array repetitions.
  subtype register_top_level_registers_range is natural range 0 to 19;

  -- Register indexes, within the list of registers.
  constant register_top_level_config : natural := 0;
  constant register_top_level_command : natural := 1;
  constant register_top_level_status : natural := 2;
  constant register_top_level_irq_status : natural := 3;
  constant register_top_level_irq_mask : natural := 4;
  function register_top_level_registers_registers(
    array_index : register_top_level_registers_range
  ) return register_top_level_reg_range;

  -- Declare 'reg_map' and 'regs_init' constants here but define them in body (deferred constants).
  -- So that functions have been elaborated when they are called.
  -- Needed for ModelSim compilation to pass.

  -- To be used as the 'regs' generic of 'axi_lite_reg_file.vhd'.
  constant register_top_level_reg_map : reg_definition_vec_t(register_top_level_reg_range);

  -- To be used for the 'regs_up' and 'regs_down' ports of 'axi_lite_reg_file.vhd'.
  subtype register_top_level_regs_t is reg_vec_t(register_top_level_reg_range);
  -- To be used as the 'default_values' generic of 'axi_lite_reg_file.vhd'.
  constant register_top_level_regs_init : register_top_level_regs_t;

  -- To be used for the 'reg_was_read' and 'reg_was_written' ports of 'axi_lite_reg_file.vhd'.
  subtype register_top_level_reg_was_accessed_t is std_ulogic_vector(register_top_level_reg_range);

  -- -----------------------------------------------------------------------------
  -- Fields in the 'registers' register within the 'registers' register array.
  -- Range of the 'field' field.
  subtype register_top_level_registers_registers_field is natural range 15 downto 0;
  -- Width of the 'field' field.
  constant register_top_level_registers_registers_field_width : positive := 16;
  -- Type for the 'field' field.
  subtype register_top_level_registers_registers_field_t is u_unsigned(15 downto 0);
  -- Default value of the 'field' field.
  constant register_top_level_registers_registers_field_init : register_top_level_registers_registers_field_t := "0000000000000000";

end package;

package body register_top_level_regs_pkg is

  function register_top_level_registers_registers(
    array_index : register_top_level_registers_range
  ) return register_top_level_reg_range is
  begin
    return 5 + array_index * 1 + 0;
  end function;

  constant register_top_level_reg_map : reg_definition_vec_t(register_top_level_reg_range) := (
    0 => (idx => register_top_level_config, reg_type => r_w),
    1 => (idx => register_top_level_command, reg_type => wpulse),
    2 => (idx => register_top_level_status, reg_type => r),
    3 => (idx => register_top_level_irq_status, reg_type => r_wpulse),
    4 => (idx => register_top_level_irq_mask, reg_type => r_w),
    5 => (idx => register_top_level_registers_registers(0), reg_type => r_wpulse),
    6 => (idx => register_top_level_registers_registers(1), reg_type => r_wpulse),
    7 => (idx => register_top_level_registers_registers(2), reg_type => r_wpulse),
    8 => (idx => register_top_level_registers_registers(3), reg_type => r_wpulse),
    9 => (idx => register_top_level_registers_registers(4), reg_type => r_wpulse),
    10 => (idx => register_top_level_registers_registers(5), reg_type => r_wpulse),
    11 => (idx => register_top_level_registers_registers(6), reg_type => r_wpulse),
    12 => (idx => register_top_level_registers_registers(7), reg_type => r_wpulse),
    13 => (idx => register_top_level_registers_registers(8), reg_type => r_wpulse),
    14 => (idx => register_top_level_registers_registers(9), reg_type => r_wpulse),
    15 => (idx => register_top_level_registers_registers(10), reg_type => r_wpulse),
    16 => (idx => register_top_level_registers_registers(11), reg_type => r_wpulse),
    17 => (idx => register_top_level_registers_registers(12), reg_type => r_wpulse),
    18 => (idx => register_top_level_registers_registers(13), reg_type => r_wpulse),
    19 => (idx => register_top_level_registers_registers(14), reg_type => r_wpulse),
    20 => (idx => register_top_level_registers_registers(15), reg_type => r_wpulse),
    21 => (idx => register_top_level_registers_registers(16), reg_type => r_wpulse),
    22 => (idx => register_top_level_registers_registers(17), reg_type => r_wpulse),
    23 => (idx => register_top_level_registers_registers(18), reg_type => r_wpulse),
    24 => (idx => register_top_level_registers_registers(19), reg_type => r_wpulse)
  );

  constant register_top_level_regs_init : register_top_level_regs_t := (
    0 => "00000000000000000000000000000000",
    1 => "00000000000000000000000000000000",
    2 => "00000000000000000000000000000000",
    3 => "00000000000000000000000000000000",
    4 => "00000000000000000000000000000000",
    5 => "00000000000000000000000000000000",
    6 => "00000000000000000000000000000000",
    7 => "00000000000000000000000000000000",
    8 => "00000000000000000000000000000000",
    9 => "00000000000000000000000000000000",
    10 => "00000000000000000000000000000000",
    11 => "00000000000000000000000000000000",
    12 => "00000000000000000000000000000000",
    13 => "00000000000000000000000000000000",
    14 => "00000000000000000000000000000000",
    15 => "00000000000000000000000000000000",
    16 => "00000000000000000000000000000000",
    17 => "00000000000000000000000000000000",
    18 => "00000000000000000000000000000000",
    19 => "00000000000000000000000000000000",
    20 => "00000000000000000000000000000000",
    21 => "00000000000000000000000000000000",
    22 => "00000000000000000000000000000000",
    23 => "00000000000000000000000000000000",
    24 => "00000000000000000000000000000000"
  );

end package body;
