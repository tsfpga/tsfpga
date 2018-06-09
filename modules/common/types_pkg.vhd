library ieee;
use ieee.std_logic_1164.all;


package types_pkg is

  type boolean_vec_t is array (integer range <>) of boolean;

  function to_sl(value : boolean) return std_logic;

end package;

package body types_pkg is

  function to_sl(value : boolean) return std_logic is
  begin
    if value then
      return '1';
    end if;
    return '0';
  end function;

end package body;
