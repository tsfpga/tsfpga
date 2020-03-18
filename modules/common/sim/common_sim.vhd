-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
context vunit_lib.vunit_context;

library osvvm;
use osvvm.RandomPkg.all;


package common_sim is

  procedure random_integer_array(
    rnd : inout RandomPType;
    integer_array : inout integer_array_t;
    length : integer;
    bit_width : integer);

end package;

package body common_sim is

  procedure random_integer_array(
    rnd : inout RandomPType;
    integer_array : inout integer_array_t;
    length : integer;
    bit_width : integer) is
  begin
    integer_array := new_1d(length, bit_width => bit_width, is_signed => false);
    for i in 0 to length - 1 loop
      set(integer_array, i, rnd.RandInt(2**bit_width - 1));
    end loop;
  end procedure;

end package body;
