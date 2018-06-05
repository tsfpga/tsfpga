library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;


package math_pkg is

  function log2(value : integer) return integer;
  function num_bits_needed(value : integer) return integer;

  function lt_0(value : signed) return boolean;
  function geq_0(value : signed) return boolean;

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
    constant result : integer := maximum(1, clog2_result); -- Special case: value 1 needs one bit.
  begin
    -- The number of bits needed to express the given value in an unsigned vector.
    assert value <= 2**result - 1 report "Calculated value not correct: " & to_string(value) & " " & to_string(result) severity failure;
    return result;
  end function;

  function lt_0(value : signed) return boolean is
  begin
    -- Vivado synthesis engine has been show to produce a lot of logic (20-30 LUTs) when doing
    -- doing simply "if value < 0 then ...", hence this bit operation is used instead.
    return value(value'left) = '1';
  end function;

  function geq_0(value : signed) return boolean is
  begin
    -- Vivado synthesis engine has been show to produce a lot of logic (20-30 LUTs) when doing
    -- doing simply "if value < 0 then ...", hence this bit operation is used instead.
    return value(value'left) = '0';
  end function;

end package body;
