-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project, a project platform for modern FPGA development.
-- https://tsfpga.com
-- https://github.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library vunit_lib;
use vunit_lib.memory_pkg.memory_t;
use vunit_lib.memory_pkg.new_memory;


package block_design_mock_pkg is

  constant axi_memory : memory_t := new_memory;

end;
