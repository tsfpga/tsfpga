-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Settings in the Zynq block design.
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.numeric_std.all;
use ieee.std_logic_1164.all;

library common;
use common.addr_pkg.all;

use work.register_top_level_regs_pkg.all;


package register_top_level_pkg is

  function get_base_addresses return addr_vec_t;
  constant base_addresses : addr_vec_t(0 to register_top_level_constant_num_register_lists - 1);

end package;

package body register_top_level_pkg is

  function get_base_addresses return addr_vec_t is
    variable result : addr_vec_t(0 to register_top_level_constant_num_register_lists - 1) := (
      others => (others => '0')
    );
  begin
    for index in result'range loop
      result(index) := to_unsigned(65536 * index, result(index)'length);
    end loop;

    return result;
  end get_base_addresses;

  constant base_addresses : addr_vec_t(0 to register_top_level_constant_num_register_lists - 1) := (
    get_base_addresses
  );

end package body;
