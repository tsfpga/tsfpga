-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library vunit_lib;
use vunit_lib.bus_master_pkg.all;
use vunit_lib.memory_pkg.all;


package top_level_sim_pkg is

  constant regs_axi_master : bus_master_t := new_bus(data_length => 32, address_length => 32);
  constant axi_memory : memory_t := new_memory;

end;
