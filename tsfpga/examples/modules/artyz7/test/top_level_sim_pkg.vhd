-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library vunit_lib;
use vunit_lib.bus_master_pkg.all;
use vunit_lib.memory_pkg.all;

library axi;
use axi.axi_lite_pkg.all;

use work.artyz7_top_pkg.all;


package top_level_sim_pkg is

  constant axi_memory : memory_t := new_memory;

end;
