library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
use vunit_lib.random_pkg.all;
context vunit_lib.vunit_context;
context vunit_lib.data_types_context;

library osvvm;
use osvvm.RandomPkg.all;


entity tb_fifo is
  generic (
    width : integer;
    depth : integer;
    runner_cfg : string
  );
end entity;

architecture tb of tb_fifo is

  constant almost_full_level : integer := depth / 2;
  constant almost_empty_level : integer := depth / 4;

  signal clk : std_logic := '0';

  signal read_ready, read_valid, almost_empty : std_logic := '0';
  signal write_ready, write_valid, almost_full : std_logic := '0';
  signal read_data, write_data : std_logic_vector(width - 1 downto 0) := (others => '0');
  signal queue : queue_t := new_queue;

begin

  test_runner_watchdog(runner, 2 ms);
  clk <= not clk after 2 ns;


  ------------------------------------------------------------------------------
  main : process
    variable rnd : RandomPType;
    variable data : integer_vector_ptr_t := null_ptr;

    procedure write_vector is
    begin
      for i in 0 to length(data) - 1 loop
        write_valid <= '1';
        write_data <= std_logic_vector(to_unsigned(get(data, i), width));
        wait until (write_ready and write_valid) = '1' and rising_edge(clk);
      end loop;
      write_valid <= '0';
    end procedure;

    procedure read_vector is
    begin
      for i in 0 to length(data) - 1 loop
        read_ready <= '1';
        wait until (read_ready and read_valid) = '1' and rising_edge(clk);
        check_equal(to_integer(unsigned(read_data)), get(data, i));
      end loop;
      read_ready <= '0';
    end procedure;

    procedure write_read_vector is
      variable stimuli_data : std_logic_vector(width - 1 downto 0);
    begin
      for i in 0 to length(data) - 1 loop
        write_valid <= '1';
        read_ready <= '1'; -- set ready before valid

        stimuli_data := std_logic_vector(to_unsigned(get(data, i), width));
        write_data <= stimuli_data;
        push(queue, stimuli_data);

        loop
          wait until rising_edge(clk);
          if (read_ready and read_valid) = '1' then
            check_equal(read_data, pop_std_ulogic_vector(queue));
          end if;
          exit when (write_ready and write_valid) = '1';
        end loop;
      end loop;
      write_valid <= '0';

      loop
        wait until rising_edge(clk);
        exit when read_valid = '0';
        check_equal(read_data, pop_std_ulogic_vector(queue));
      end loop;
      read_ready <= '0';

      check(is_empty(queue));
    end procedure;

    procedure test_almost_full is
    begin
      for i in 0 to almost_full_level - 1 loop
        write_valid <= '1';
        wait until (write_ready and write_valid) = '1' and rising_edge(clk);
        check_equal(almost_full, '0');
      end loop;
      write_valid <= '0';

      wait until rising_edge(clk);
      check_equal(almost_full, '1');

      for i in 0 to almost_full_level - 1 loop
        read_ready <= '1';
        wait until (read_ready and read_valid) = '1' and rising_edge(clk);

        if i = 0 then
          -- The flag switches after a one cycle delay. So for the first read we have to wait an extra cycle.
          read_ready <= '0';
          wait until rising_edge(clk);
          read_ready <= '1';
        end if;

        check_equal(almost_full, '0');
      end loop;
      read_ready <= '0';
    end procedure;

    procedure test_almost_empty is
    begin
      for i in 0 to almost_empty_level - 1 loop
        write_valid <= '1';
        wait until (write_ready and write_valid) = '1' and rising_edge(clk);
        check_equal(almost_empty, '1');
      end loop;
      write_valid <= '0';

      wait until rising_edge(clk);
      check_equal(almost_empty, '0');

      for i in 0 to almost_empty_level - 1 loop
        read_ready <= '1';
        wait until (read_ready and read_valid) = '1' and rising_edge(clk);

        if i = 0 then
          -- The flag switches after a one cycle delay. So for the first read we have to wait an extra cycle.
          read_ready <= '0';
          wait until rising_edge(clk);
          read_ready <= '1';
        end if;

        check_equal(almost_empty, '1');
      end loop;
      read_ready <= '0';
    end procedure;

  begin
    test_runner_setup(runner, runner_cfg);
    rnd.InitSeed(rnd'instance_name);

    if run("fill_fifo") then
      for i in 0 to 4 loop
        random_integer_vector_ptr(rnd, data, length=>depth, bits_per_word=>width, is_signed=>false);

        write_vector;
        wait until rising_edge(clk);
        check_equal(write_ready, '0', "Should be full");

        read_vector;
        wait until rising_edge(clk);
        check_equal(read_valid, '0', "Should be empty");
      end loop;

    elsif run("test_almost_full") then
      for i in 0 to 4 loop
        test_almost_full;
      end loop;

    elsif run("test_almost_empty") then
      for i in 0 to 4 loop
        test_almost_empty;
      end loop;

    elsif run("test_read_before_valid") then
      random_integer_vector_ptr(rnd, data, length=>depth, bits_per_word=>width, is_signed=>false);
      write_read_vector;
    end if;

    test_runner_cleanup(runner);
  end process;


  ------------------------------------------------------------------------------
  dut : entity work.fifo
    generic map (
      width => width,
      depth => depth,
      almost_full_level => almost_full_level,
      almost_empty_level => almost_empty_level
    )
    port map (
      clk => clk,

      read_ready => read_ready,
      read_valid => read_valid,
      read_data => read_data,
      almost_empty => almost_empty,

      write_ready => write_ready,
      write_valid => write_valid,
      write_data => write_data,
      almost_full => almost_full
    );

end architecture;
