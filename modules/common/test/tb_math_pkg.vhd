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
  begin
    test_runner_setup(runner, runner_cfg);

    check_equal(log2(32), 5);
    check_equal(log2(64), 6);
    check_equal(log2(128), 7);

    test_runner_cleanup(runner);
  end process;

end architecture;
