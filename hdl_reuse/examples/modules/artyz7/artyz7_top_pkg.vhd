library ieee;
use ieee.std_logic_1164.all;

library common;
use common.addr_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.all;


package artyz7_top_pkg is

  constant reg_slaves : addr_and_mask_vec_t(0 to 12 - 1) := (
    0 => (addr => x"0000_0000", mask => x"0000_f000"),
    1 => (addr => x"0000_1000", mask => x"0000_f000"),
    2 => (addr => x"0000_2000", mask => x"0000_f000"),
    3 => (addr => x"0000_3000", mask => x"0000_f000"),
    4 => (addr => x"0000_4000", mask => x"0000_f000"),
    5 => (addr => x"0000_5000", mask => x"0000_f000"),
    6 => (addr => x"0000_6000", mask => x"0000_f000"),
    7 => (addr => x"0000_7000", mask => x"0000_f000"),
    8 => (addr => x"0000_8000", mask => x"0000_f000"),
    9 => (addr => x"0000_9000", mask => x"0000_f000"),
    10 => (addr => x"0000_a000", mask => x"0000_f000"),
    11 => (addr => x"0000_b000", mask => x"0000_f000")
  );

end;
