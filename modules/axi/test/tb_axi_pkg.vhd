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

use work.axi_pkg.all;


entity tb_axi_pkg is
  generic (
    data_width : integer;
    id_width : integer;
    runner_cfg : string
  );
end entity;

architecture tb of tb_axi_pkg is
begin

  main : process
    variable rnd : RandomPType;

    variable data_a : axi_m2s_a_t;
    variable data_a_slv, data_a_converted : std_logic_vector(axi_m2s_a_sz(id_width) - 1 downto 0) := (others => '0');

    variable data_w : axi_m2s_w_t := axi_m2s_w_init;
    variable data_w_slv, data_w_converted : std_logic_vector(axi_m2s_w_sz(data_width) - 1 downto 0);

    variable data_r : axi_s2m_r_t := axi_s2m_r_init;
    variable data_r_slv, data_r_converted : std_logic_vector(axi_s2m_r_sz(data_width, id_width) - 1 downto 0);

    variable data_b : axi_s2m_b_t := axi_s2m_b_init;
    variable data_b_slv, data_b_converted : std_logic_vector(axi_s2m_b_sz(id_width) - 1 downto 0);
  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    for i in 0 to 1000 loop
      -- Loop a couple of times to get good random coverage

      data_a_slv := rnd.RandSLV(data_a_slv'length);
      data_a := to_axi_m2s_a(data_a_slv, id_width);
      data_a_converted := to_slv(data_a, id_width);

      check_equal(data_a_converted, data_a_slv);

      data_w_slv := rnd.RandSLV(data_w_slv'length);
      data_w := to_axi_m2s_w(data_w_slv, data_width);
      data_w_converted := to_slv(data_w, data_width);

      check_equal(data_w_converted, data_w_slv);

      data_r_slv := rnd.RandSLV(data_r_slv'length);
      data_r := to_axi_s2m_r(data_r_slv, data_width, id_width);
      data_r_converted := to_slv(data_r, data_width, id_width);

      check_equal(data_r_converted, data_r_slv);

      data_b_slv := rnd.RandSLV(data_b_slv'length);
      data_b := to_axi_s2m_b(data_b_slv, id_width);
      data_b_converted := to_slv(data_b, id_width);

      check_equal(data_b_converted, data_b_slv);
    end loop;

    test_runner_cleanup(runner);
  end process;

end architecture;
