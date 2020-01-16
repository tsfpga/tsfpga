-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;


package addr_pkg is

  constant addr_width : integer := 32;
  subtype addr_t is std_logic_vector(addr_width - 1 downto 0);

  type addr_and_mask_t is record
    addr : addr_t;
    mask : addr_t;
  end record;
  type addr_and_mask_vec_t is array (integer range <>) of addr_and_mask_t;

  function match(addr : std_logic_vector; addr_and_mask : addr_and_mask_t) return boolean;
  function decode(addr : std_logic_vector; addrs : addr_and_mask_vec_t) return integer;

end package;

package body addr_pkg is

  function match(addr : std_logic_vector; addr_and_mask : addr_and_mask_t) return boolean is
    variable test_ok : boolean := true;
  begin
    for bit_idx in addr_and_mask.addr'range loop
      if addr_and_mask.mask(bit_idx) then
        test_ok := test_ok and (addr(bit_idx) = addr_and_mask.addr(bit_idx));
      end if;
    end loop;

    return test_ok;
  end function;

  function decode(addr : std_logic_vector; addrs : addr_and_mask_vec_t) return integer is
    constant decode_fail : integer := addrs'length;
  begin
    for addr_idx in addrs'range loop
      if match(addr, addrs(addr_idx)) then
        return addr_idx;
      end if;
    end loop;

    return decode_fail;
  end function;

end package body;
