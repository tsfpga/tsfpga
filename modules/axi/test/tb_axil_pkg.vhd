-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

library osvvm;
use osvvm.RandomPkg.all;

use work.axil_pkg.all;


entity tb_axil_pkg is
  generic (
    data_width : integer;
    addr_width : integer := 32;
    runner_cfg : string
  );
end entity;

architecture tb of tb_axil_pkg is
begin

  main : process
    variable rnd : RandomPType;

    variable data_a : axil_m2s_a_t;
    variable data_a_slv, data_a_converted : std_logic_vector(axil_m2s_a_sz(addr_width) - 1 downto 0) := (others => '0');

    variable data_w : axil_m2s_w_t := axil_m2s_w_init;
    variable data_w_slv, data_w_converted : std_logic_vector(axil_m2s_w_sz(data_width) - 1 downto 0);

    variable data_r : axil_s2m_r_t := axil_s2m_r_init;
    variable data_r_slv, data_r_converted : std_logic_vector(axil_s2m_r_sz(data_width) - 1 downto 0);
  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    -- Loop a couple of times to get good random coverage
    for i in 0 to 1000 loop
      data_w_slv := rnd.RandSLV(data_w_slv'length);
      data_w := to_axil_m2s_w(data_w_slv, data_width);
      data_w_converted := to_slv(data_w, data_width);

      check_equal(data_w_converted, data_w_slv);

      data_r_slv := rnd.RandSLV(data_r_slv'length);
      data_r := to_axil_s2m_r(data_r_slv, data_width);
      data_r_converted := to_slv(data_r, data_width);

      check_equal(data_r_converted, data_r_slv);
    end loop;

    test_runner_cleanup(runner);
  end process;

end architecture;
