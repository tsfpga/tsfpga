-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;


package types_pkg is

  -- Similar to integer_vector available in VHDL
  type natural_vector is array (integer range <>) of natural;
  type positive_vector is array (integer range <>) of positive;

  type boolean_vec_t is array (integer range <>) of boolean;

  function to_sl(value : boolean) return std_logic;
  function to_bool(value : std_logic) return boolean;
  function to_int(value : boolean) return integer;
  function to_int(value : std_logic) return integer;

  function swap_bytes(data : std_logic_vector) return std_logic_vector;

end package;

package body types_pkg is

  function to_sl(value : boolean) return std_logic is
  begin
    if value then
      return '1';
    end if;
    return '0';
  end function;

  function to_bool(value : std_logic) return boolean is
  begin
    if value = '1' then
      return true;
    elsif value = '0' then
      return false;
    end if;
    assert false report "Can not convert value " & to_string(value) severity failure;
    return false;
  end function;

  function to_int(value : boolean) return integer is
  begin
    if value then
      return 1;
    else
      return 0;
    end if;
  end function;

  function to_int(value : std_logic) return integer is
  begin
    if value = '1' then
      return 1;
    elsif value = '0' then
      return 0;
    end if;

    assert false report "Can not convert value " & to_string(value) severity failure;
    return 0;
  end function;

  function swap_bytes(data : std_logic_vector) return std_logic_vector is
    variable result : std_logic_vector(data'range);
    constant num_bytes : integer := data'length / 8;
    variable result_byte_idx : integer;
  begin
    -- Swap endianness of the input word

    assert data'left > data'right report "Only use with descending range" severity failure;
    assert data'length mod 8 = 0 report "Must be a whole number of bytes" severity failure;

    for input_byte_idx in 0 to num_bytes - 1 loop
      result_byte_idx := num_bytes - 1 - input_byte_idx;
      result(result_byte_idx * 8 + 7 downto result_byte_idx * 8) :=
        data(input_byte_idx * 8 + 7 downto input_byte_idx * 8);
    end loop;

    return result;
  end function;

end package body;
