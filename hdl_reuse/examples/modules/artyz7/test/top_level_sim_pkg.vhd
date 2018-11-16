library vunit_lib;
use vunit_lib.bus_master_pkg.all;


package top_level_sim_pkg is

  constant register_axi_master : bus_master_t := new_bus(data_length => 32, address_length => 32);

end;
