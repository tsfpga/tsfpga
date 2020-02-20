-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

use work.types_pkg.all;


entity tb_types_pkg is
  generic (
    runner_cfg : string
  );
end entity;

architecture tb of tb_types_pkg is
begin

  main : process

    variable input_data, expected : std_logic_vector(4 * 8 - 1 downto 0);

  begin
    test_runner_setup(runner, runner_cfg);

    if run("test_swap_bytes") then
      input_data := x"01_23_45_67";
      expected := x"67_45_23_01";
      check_equal(swap_bytes(input_data), expected);
    elsif run("test_to_bool") then
      check_equal(to_bool('0'), false);
      check_equal(to_bool('1'), true);
    end if;

    test_runner_cleanup(runner);
  end process;

end architecture;
