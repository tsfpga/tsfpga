library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

use work.math_pkg.all;


entity tb_math_pkg is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_math_pkg is
begin

  main : process
    variable value : signed(5 - 1 downto 0);
  begin
    test_runner_setup(runner, runner_cfg);

    if run("log2") then
      check_equal(log2(32), 5);
      check_equal(log2(64), 6);
      check_equal(log2(128), 7);
    elsif run("num_bits_needed") then
      check_equal(num_bits_needed(6), 3);
      check_equal(num_bits_needed(7), 3);
      check_equal(num_bits_needed(8), 4);
      check_equal(num_bits_needed(9), 4);

      check_equal(num_bits_needed(0), 1);
    elsif run("lt_0") then
      value := to_signed(-3, value'length);
      check_true(lt_0(value));
      value := to_signed(0, value'length);
      check_false(lt_0(value));
      value := to_signed(3, value'length);
      check_false(lt_0(value));
    elsif run("geq_0") then
      value := to_signed(-3, value'length);
      check_false(geq_0(value));
      value := to_signed(0, value'length);
      check_true(geq_0(value));
      value := to_signed(3, value'length);
      check_true(geq_0(value));
    end if;

    test_runner_cleanup(runner);
  end process;

end architecture;
