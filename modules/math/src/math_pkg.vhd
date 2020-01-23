-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;


package math_pkg is

  function log2(value            : integer) return integer;
  function num_bits_needed(value : integer) return integer;
  function is_power_of_two(value : integer) return boolean;

  function lt_0(value  : signed) return boolean;
  function geq_0(value : signed) return boolean;

  function to_gray(value, num_bits : integer) return std_logic_vector;
  function from_gray(code          : std_logic_vector) return integer;

end package;

package body math_pkg is

  function log2(value : integer) return integer is
    constant result : integer := integer(log2(real(value)));
  begin
    assert 2**result = value report "Calculated value not correct" severity failure;
    return result;
  end function;

  function num_bits_needed(value : integer) return integer is
    constant clog2_result : integer := integer(ceil(log2(real(value + 1))));
    constant result       : integer := maximum(1, clog2_result);  -- Special case: value 1 needs one bit.
  begin
    -- The number of bits needed to express the given value in an unsigned vector.
    assert value <= 2**result - 1 report "Calculated value not correct: " & to_string(value) & " " & to_string(result) severity failure;
    return result;
  end function;

  function is_power_of_two(value : integer) return boolean is
  begin
    return 2**log2(value) = value;
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

  function to_gray(value, num_bits : integer) return std_logic_vector is
    variable value_slv : std_logic_vector(num_bits - 1 downto 0);
    variable ret       : std_logic_vector(num_bits - 1 downto 0);
  begin
    assert value < 2**num_bits report "Input value is out of range: " & to_string(value);

    value_slv := std_logic_vector(to_unsigned(value, num_bits));
    ret       := value_slv xor "0" & value_slv(value_slv'high downto 1);
    return ret;
  end function;

  function from_gray(code : std_logic_vector) return integer is
    variable ret_slv : std_logic_vector(code'range);
    variable ret     : integer range 0 to 2**code'length-1;
  begin
    ret_slv(code'high) := code(code'high);
    for bit_num in code'high -1 downto 0 loop
      ret_slv(bit_num) := ret_slv(bit_num + 1) xor code(bit_num);
    end loop;

    ret := to_integer(unsigned(ret_slv));
    return ret;
  end function;

end package body;
