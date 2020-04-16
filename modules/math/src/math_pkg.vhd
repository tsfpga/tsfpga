-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;


package math_pkg is

  function log2(value            : integer) return integer;
  function is_power_of_two(value : integer) return boolean;

  function num_bits_needed(value : integer) return integer;
  function num_bits_needed(value : std_logic_vector) return integer;

  function lt_0(value  : signed) return boolean;
  function geq_0(value : signed) return boolean;

  function to_gray(value : unsigned) return std_logic_vector;
  function from_gray(code : std_logic_vector) return unsigned;

end package;

package body math_pkg is

  function log2_no_assert(value : integer) return integer is
  begin
    return integer(log2(real(value)));
  end function;

  function log2(value : integer) return integer is
  begin
    assert is_power_of_two(value) report "Must be power of two: " & to_string(value) severity failure;
    return log2_no_assert(value);
  end function;

  function is_power_of_two(value : integer) return boolean is
    constant log2_value : integer := log2_no_assert(value);
  begin
    return 2 ** log2_value = value;
  end function;

  function num_bits_needed(value : std_logic_vector) return integer is
    variable result : integer;
  begin
    -- The number of bits needed to express the given value.
    assert value'high > value'low report "Use only with descending range" severity failure;
    assert value'low = 0 report "Use vector that starts at zero" severity failure;

    for bit_idx in value'high downto value'low loop
      if value(bit_idx) = '1' then
        return bit_idx + 1;
      end if;
    end loop;
    return 1;
  end function;

  function num_bits_needed(value : integer) return integer is
    constant value_slv : std_logic_vector(64 - 1 downto 0) := std_logic_vector(to_unsigned(value, 64));
    constant result : integer := num_bits_needed(value_slv);
  begin
    -- The number of bits needed to express the given value in an unsigned vector.
    assert value <= 2**result - 1 report "Calculated value not correct: " & to_string(value) & " " & to_string(result) severity failure;
    return result;
  end function;

  function lt_0(value : signed) return boolean is
  begin
    -- The Vivado synthesis engine has been shown to produce a lot of logic (20-30 LUTs) when
    -- doing simply "if value < 0 then ...", hence this bit operation is used instead.
    return value(value'left) = '1';
  end function;

  function geq_0(value : signed) return boolean is
  begin
    -- The Vivado synthesis engine has been shown to produce a lot of logic (20-30 LUTs) when
    -- doing simply "if value < 0 then ...", hence this bit operation is used instead.
    return value(value'left) = '0';
  end function;

  function to_gray(value : unsigned) return std_logic_vector is
    variable value_slv, result : std_logic_vector(value'range);
  begin
    value_slv := std_logic_vector(value);
    result := value_slv xor "0" & value_slv(value_slv'high downto 1);
    return result;
  end function;

  function from_gray(code : std_logic_vector) return unsigned is
    variable result : unsigned(code'range);
  begin
    result(code'high) := code(code'high);
    for bit_num in code'high -1 downto 0 loop
      result(bit_num) := result(bit_num + 1) xor code(bit_num);
    end loop;

    return result;
  end function;

end package body;
