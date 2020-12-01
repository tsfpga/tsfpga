-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Wrapper that sets an appropriate generic.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library axi;
use axi.axil_pkg.all;

-- TODO there is some problem in our formal flow related to the work library.
-- Doing simply "use work.reg_file_pkg.all;" does not work here. The issue seems to be
-- isolated to the top level however, since axil_reg_file.vhd uses "work" completely fine.
--
-- Appending "--work=reg_file" in the sby_writer.py ghdl elaborate call did not immediately solve
-- the issue.
library reg_file;
use reg_file.reg_file_pkg.all;


entity axil_reg_file_formal_wrapper is
  port (
    clk : in std_logic;
    --
    axil_m2s : in axil_m2s_t;
    axil_s2m : out axil_s2m_t;
    --
    regs_up : in reg_vec_t(0 to 9);
    regs_down : out reg_vec_t(0 to 9);
    --
    reg_was_read : out std_logic_vector(0 to 9);
    reg_was_written : out std_logic_vector(0 to 9)
  );
end entity;

architecture a of axil_reg_file_formal_wrapper is

  constant regs : reg_definition_vec_t(regs_up'range) := (
    (idx=>0, reg_type=>r),
    (idx=>1, reg_type=>w),
    (idx=>2, reg_type=>r_w),
    (idx=>3, reg_type=>wpulse),
    (idx=>4, reg_type=>r_wpulse),
    (idx=>5, reg_type=>r),
    (idx=>6, reg_type=>w),
    (idx=>7, reg_type=>r_w),
    (idx=>8, reg_type=>wpulse),
    (idx=>9, reg_type=>r_wpulse)
  );

begin

  axil_reg_file_inst : entity reg_file.axil_reg_file
    generic map (
        regs => regs
    )
    port map (
      clk => clk,
      --
      axil_m2s => axil_m2s,
      axil_s2m => axil_s2m,
      --
      regs_up => regs_up,
      regs_down => regs_down,
      --
      reg_was_read => reg_was_read,
      reg_was_written => reg_was_written
    );


end architecture;
