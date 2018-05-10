library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
use vunit_lib.bus_master_pkg.all;
use vunit_lib.axi_pkg.all;
use vunit_lib.memory_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.com_context;

library osvvm;
use osvvm.RandomPkg.all;

library bfm;

library math;
use math.math_pkg.all;

use work.axil_pkg.all;
use work.axi_pkg.all;
use work.axi_pkg.axi_resp_okay;
use work.axi_pkg.axi_resp_slverr;


entity tb_axi_to_axil_bus_error is
  generic (
    data_width : integer;
    runner_cfg : string
  );
end entity;

architecture tb of tb_axi_to_axil_bus_error is
  signal clk : std_logic := '0';

  signal axi_read_m2s : axi_read_m2s_t := axi_read_m2s_init;
  signal axi_read_s2m : axi_read_s2m_t;

  signal axi_write_m2s : axi_write_m2s_t := axi_write_m2s_init;
  signal axi_write_s2m : axi_write_s2m_t;

  signal axil_read_m2s : axil_read_m2s_t;
  signal axil_read_s2m : axil_read_s2m_t := axil_read_s2m_init;

  signal axil_write_m2s : axil_write_m2s_t;
  signal axil_write_s2m : axil_write_s2m_t := axil_write_s2m_init;

  constant correct_size : integer := log2(data_width / 8);
  constant correct_len : integer := 0;

begin

  test_runner_watchdog(runner, 10 ms);
  clk <= not clk after 2 ns;


  ------------------------------------------------------------------------------
  main : process
    procedure test_ar(len, size : integer; resp : std_logic_vector) is
    begin
      axil_read_s2m.ar.ready <= '1';

      axi_read_m2s.ar.valid <= '1';
      axi_read_m2s.ar.len <= std_logic_vector(to_unsigned(len, axi_read_m2s.ar.len'length));
      axi_read_m2s.ar.size <= std_logic_vector(to_unsigned(size, axi_read_m2s.ar.size'length));

      wait until (axi_read_m2s.ar.valid and axi_read_s2m.ar.ready) = '1' and rising_edge(clk);
      axi_read_m2s.r.ready <= '1';
      axil_read_s2m.r.valid <= '1';

      wait until (axi_read_s2m.r.valid and axi_read_m2s.r.ready) = '1' and rising_edge(clk);
      check_equal(axi_read_s2m.r.resp, resp);
    end procedure;

    procedure test_aw(len, size : integer; resp : std_logic_vector) is
    begin
      axil_write_s2m.aw.ready <= '1';

      axi_write_m2s.aw.valid <= '1';
      axi_write_m2s.aw.len <= std_logic_vector(to_unsigned(len, axi_read_m2s.ar.len'length));
      axi_write_m2s.aw.size <= std_logic_vector(to_unsigned(size, axi_read_m2s.ar.size'length));

      wait until (axi_write_m2s.aw.valid and axi_write_s2m.aw.ready) = '1' and rising_edge(clk);
      axi_write_m2s.b.ready <= '1';
      axil_write_s2m.b.valid <= '1';

      wait until (axi_write_s2m.b.valid and axi_write_m2s.b.ready) = '1' and rising_edge(clk);
      check_equal(axi_write_s2m.b.resp, resp);
    end procedure;

  begin
    test_runner_setup(runner, runner_cfg);

    if run("ar_ok") then
      test_ar(correct_len, correct_size, axi_resp_okay);
    elsif run("ar_len_error") then
      test_ar(correct_len + 1, correct_size, axi_resp_slverr);
    elsif run("ar_size_error") then
      test_ar(correct_len, correct_size + 1, axi_resp_slverr);
    elsif run("aw_ok") then
      test_aw(correct_len, correct_size, axi_resp_okay);
    elsif run("aw_len_error") then
      test_aw(correct_len + 1, correct_size, axi_resp_slverr);
    elsif run("aw_size_error") then
      test_aw(correct_len, correct_size + 1, axi_resp_slverr);
    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.axi_to_axil
    generic map (
      data_width => data_width
    )
    port map (
      clk => clk,

      axi_read_m2s => axi_read_m2s,
      axi_read_s2m => axi_read_s2m,

      axi_write_m2s => axi_write_m2s,
      axi_write_s2m => axi_write_s2m,

      axil_read_m2s => axil_read_m2s,
      axil_read_s2m => axil_read_s2m,

      axil_write_m2s => axil_write_m2s,
      axil_write_s2m => axil_write_s2m
    );

end architecture;
