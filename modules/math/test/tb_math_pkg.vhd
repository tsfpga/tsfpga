-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

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

  -- This function calculates the number of bits pars that differs
  -- in the two input vectors.
  function hamming_distance(in1, in2 : std_logic_vector) return integer is
    variable tmp : std_logic_vector(in1'range);
    variable ret : integer := 0;
  begin
    tmp := in1 xor in2;
    for i in tmp'range loop
      if tmp(i) = '1' then
        ret := ret + 1;
      end if;
    end loop;
    return ret;
  end function;
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
      check_equal(num_bits_needed(0), 1);
      check_equal(num_bits_needed(1), 1);
      check_equal(num_bits_needed(2), 2);
      check_equal(num_bits_needed(3), 2);

      check_equal(num_bits_needed(6), 3);
      check_equal(num_bits_needed(7), 3);
      check_equal(num_bits_needed(8), 4);
      check_equal(num_bits_needed(9), 4);
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
    elsif run("to_and_from_gray") then
      for i in 1 to 2**8-2 loop
        check_equal(from_gray(to_gray(i, 8)), i);
        -- Verify that only one bit changes when incrementing the input
        -- to to_gray
        check_equal(hamming_distance(to_gray(i, 8), to_gray(i+1, 8)), 1);
        check_equal(hamming_distance(to_gray(i-1, 8), to_gray(i, 8)), 1);
        check_equal(hamming_distance(to_gray(i-1, 8), to_gray(i+1, 8)), 2);
      end loop;
    end if;

    test_runner_cleanup(runner);
  end process;

end architecture;
