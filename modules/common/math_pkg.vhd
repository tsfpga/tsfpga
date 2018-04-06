library ieee;
use ieee.std_logic_1164.all;
use ieee.math_real.all;


package math_pkg is

  function log2(value : integer) return integer;

end package;

package body math_pkg is

  function log2(value : integer) return integer is
    variable result : integer := integer(log2(real(value)));
  begin
    assert 2**result = value report "Calculated value not correct";
    return result;
  end function;

end package body;
