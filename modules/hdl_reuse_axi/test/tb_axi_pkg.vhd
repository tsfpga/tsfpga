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
    runner_cfg : string
  );
end entity;

architecture tb of tb_axi_pkg is
begin

  main : process
    variable rnd : RandomPType;

    variable data_a, data_a_converted : axi_m2s_a_t := axi_m2s_a_init;
    variable data_a_slv : std_logic_vector(axi_m2s_a_sz - 1 downto 0);

    variable data_w, data_w_converted : axi_m2s_w_t := axi_m2s_w_init;
    variable data_w_slv : std_logic_vector(axi_m2s_w_sz(data_width) - 1 downto 0);
    subtype w_strb_rng is integer range axi_w_strb_sz(data_width) - 1 downto 0;

    variable data_r, data_r_converted : axi_s2m_r_t := axi_s2m_r_init;
    variable data_r_slv : std_logic_vector(axi_s2m_r_sz(data_width) - 1 downto 0);
  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    while test_suite loop
      if run("a") then
        data_a.addr := rnd.RandSLV(data_a.addr'length);
        data_a.len := rnd.RandSLV(data_a.len'length);
        data_a.size := rnd.RandSLV(data_a.size'length);
        data_a.burst := rnd.RandSLV(data_a.burst'length);

        data_a_slv := to_slv(data_a);

        data_a_converted := to_axi_m2s_a(data_a_slv);
        data_a_converted.valid := '0';

        assert data_a_converted = data_a;
      elsif run("w") then
        data_w.data(data_width - 1 downto 0) := rnd.RandSLV(data_width);
        data_w.strb(w_strb_rng) := rnd.RandSLV(axi_w_strb_sz(data_width));
        data_w.last := '1';

        data_w_slv := to_slv(data_w, data_width);

        data_w_converted := to_axi_m2s_w(data_w_slv, data_width);

        assert data_w.strb(w_strb_rng) = data_w_converted.strb(w_strb_rng);
        assert data_w.last = data_w_converted.last;
        assert data_w.data(data_width - 1 downto 0) = data_w_converted.data(data_width - 1 downto 0);
      elsif run("r") then
        data_r.data(data_width - 1 downto 0) := rnd.RandSLV(data_width);
        data_r.resp := rnd.RandSLV(axi_resp_sz);
        data_r.last := '1';

        data_r_slv := to_slv(data_r, data_width);

        data_r_converted := to_axi_s2m_r(data_r_slv, data_width);

        assert data_r.resp = data_r_converted.resp;
        assert data_r.last = data_r_converted.last;
        assert data_r.data(data_width - 1 downto 0) = data_r_converted.data(data_width - 1 downto 0);
      end if;
    end loop;

    test_runner_cleanup(runner);
  end process;

end architecture;
