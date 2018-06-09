library ieee;
use ieee.std_logic_1164.all;

library common;
use common.addr_pkg.all;

library reg_file;
use reg_file.reg_file_pkg.all;


package fpga_top_pkg is

  constant num_reg_slaves : integer := 12;
  constant reg_slaves : addr_and_mask_vec_t(0 to num_reg_slaves - 1) := (
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

  constant reg_map : reg_definition_vec_t(0 to 16 - 1) := (
    (idx => 0, reg_type => r_w),
    (idx => 1, reg_type => r_w),
    (idx => 2, reg_type => r_w),
    (idx => 3, reg_type => w),
    (idx => 4, reg_type => w),
    (idx => 5, reg_type => w),
    (idx => 6, reg_type => r),
    (idx => 7, reg_type => r),
    (idx => 8, reg_type => r),
    (idx => 9, reg_type => wpulse),
    (idx => 10, reg_type => wpulse),
    (idx => 11, reg_type => wpulse),
    (idx => 12, reg_type => r_wpulse),
    (idx => 13, reg_type => r_wpulse),
    (idx => 14, reg_type => r_wpulse),
    (idx => 15, reg_type => r_wpulse)
  );

end;
