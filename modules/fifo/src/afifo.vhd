-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------
-- Asynchronous FIFO.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library common;
use common.attribute_pkg.all;
use common.types_pkg.all;

library math;
use math.math_pkg.all;

library resync;


entity afifo is
  generic (
    width : positive;
    depth : positive;
    -- Changing these levels from default value will increase logic footprint
    almost_full_level : integer range 0 to depth := depth;
    almost_empty_level : integer range 0 to depth := 0;
    -- If enabled, read_valid will not be asserted until a full packet is available in
    -- FIFO. I.e. when write_last has been received.
    enable_packet_mode : boolean := false;
    -- Set to true in order to use read_last and write_last
    enable_last : boolean := enable_packet_mode;
    ram_type : ram_style_t := ram_style_auto
  );
  port (
    -- Read data interface
    clk_read : in std_logic;
    read_ready : in  std_logic;
    -- '1' if FIFO is not empty
    read_valid : out std_logic := '0';
    read_data  : out std_logic_vector(width - 1 downto 0);
    -- Must set enable_last generic in order to use this
    read_last  : out std_logic := '0';

    -- Status signals on the read side. Updated one clock cycle after read transactions.
    -- Updated "a while" after write transactions (not deterministic).
    read_level : out integer range 0 to depth := 0;
    -- '1' if there are almost_empty_level or fewer words available to read
    read_almost_empty : out std_logic;

    -- Write data interface
    clk_write : in std_logic;
    -- '1' if FIFO is not full
    write_ready : out std_logic := '1';
    write_valid : in  std_logic;
    write_data  : in  std_logic_vector(width - 1 downto 0);
    -- Must set enable_last generic in order to use this
    write_last : in std_logic := '0';

    -- Status signals on the write side. Updated one clock cycle after write transactions.
    -- Updated "a while" after read transactions (not deterministic).
    write_level : out integer range 0 to depth := 0;
    -- '1' if there are almost_full_level or more words available in the FIFO
    write_almost_full : out std_logic
  );
end entity;

architecture a of afifo is

  constant enable_last_int : boolean := enable_last or enable_packet_mode;

  -- Need one extra bit in the addresses to be able to make the distinction if the FIFO
  -- is full or empty (where the addresses would otherwise be equal).
  subtype fifo_addr_t is unsigned(num_bits_needed(2 * depth - 1) - 1 downto 0);
  signal read_addr_next, write_addr : fifo_addr_t := (others => '0');

  -- The counter for number of lasts in the FIFO (used by packet mode) also needs one extra bit,
  -- to cover the case when the whole FIFO depth has been written with lasts.
  signal num_lasts_written : fifo_addr_t := (others => '0');

  -- The part of the address that actually goes to the BRAM address port
  subtype bram_addr_range is integer range num_bits_needed(depth - 1) - 1 downto 0;

begin

  assert is_power_of_two(depth) report "Depth must be a power of two" severity failure;

  assert enable_last or (not enable_packet_mode) report "Must set enable_last for packet mode" severity failure;

  assign_almost_full : if almost_full_level = depth generate
    write_almost_full <= not write_ready;
  else generate
    write_almost_full <= to_sl(write_level > almost_full_level - 1);
  end generate;

  assign_almost_empty : if almost_empty_level = 0 generate
    read_almost_empty <= not read_valid;
  else generate
    read_almost_empty <= to_sl(read_level < almost_empty_level + 1);
  end generate;


  ------------------------------------------------------------------------------
  write : block
    signal read_addr_resync : fifo_addr_t := (others => '0');
  begin

    ------------------------------------------------------------------------------
    write_status : process
      variable write_addr_next : fifo_addr_t;
      variable current_write_level : integer range 0 to depth;
    begin
      wait until rising_edge(clk_write);

      current_write_level := to_integer(write_addr - read_addr_resync) mod (2 * depth);
      write_level <= current_write_level + to_int(write_ready and write_valid);
      num_lasts_written <= num_lasts_written + to_int(write_ready and write_valid and write_last);

      write_addr_next := write_addr + to_int(write_ready and write_valid);

      write_ready <= to_sl(
        read_addr_resync(bram_addr_range) /= write_addr_next(bram_addr_range)
        or read_addr_resync(read_addr_resync'high) =  write_addr_next(write_addr_next'high));

      write_addr <= write_addr_next;
    end process;


    ------------------------------------------------------------------------------
    resync_read_addr : entity resync.resync_counter
    generic map (
      width => read_addr_next'length
    )
    port map (
      clk_in      => clk_read,
      counter_in  => read_addr_next,
      clk_out     => clk_write,
      counter_out => read_addr_resync
    );
  end block;


  ------------------------------------------------------------------------------
  read : block
    signal write_addr_resync, read_addr : fifo_addr_t := (others => '0');
    signal num_lasts_read, num_lasts_written_resync : fifo_addr_t := (others => '0');
  begin

    ------------------------------------------------------------------------------
    read_status : process
      variable read_level_next : integer range 0 to depth;
    begin
      wait until rising_edge(clk_read);

      read_level_next := to_integer(write_addr_resync - read_addr_next) mod (2 * depth);
      if enable_packet_mode then
        read_valid <= to_sl(read_level_next /= 0 and num_lasts_read /= num_lasts_written_resync);
        num_lasts_read <= num_lasts_read + to_int(read_ready and read_valid and read_last);
      else
        read_valid <= to_sl(read_level_next /= 0);
      end if;

      read_level <= read_level_next;
      read_addr <= read_addr_next;
    end process;

    read_addr_next <= read_addr + to_int(read_ready and read_valid);


    ------------------------------------------------------------------------------
    resync_write_addr : entity resync.resync_counter
      generic map (
        width => write_addr'length
      )
      port map (
        clk_in      => clk_write,
        counter_in  => write_addr,
        clk_out     => clk_read,
        counter_out => write_addr_resync
      );


    ------------------------------------------------------------------------------
    resync_num_lasts_written : if enable_packet_mode generate
      resync_counter_inst : entity resync.resync_counter
        generic map (
          width => write_addr'length
        )
        port map (
          clk_in      => clk_write,
          counter_in  => num_lasts_written,
          clk_out     => clk_read,
          counter_out => num_lasts_written_resync
        );
    end generate;
  end block;


  ------------------------------------------------------------------------------
  memory : block
    constant memory_word_width : integer := width + to_int(enable_last_int);
    subtype word_t is std_logic_vector(memory_word_width - 1 downto 0);
    type mem_t is array (integer range <>) of word_t;

    signal mem : mem_t(0 to depth - 1) := (others => (others => '0'));
    attribute ram_style of mem : signal is to_attribute(ram_type);

    signal memory_read_data, memory_write_data : word_t;
  begin

    read_data <= memory_read_data(read_data'range);
    memory_write_data(write_data'range) <= write_data;

    assign_data : if enable_last_int generate
      read_last <= memory_read_data(memory_read_data'high);
      memory_write_data(memory_write_data'high) <= write_last;
    end generate;

    write_memory : process
    begin
      wait until rising_edge(clk_write);

      if write_ready and write_valid then
        mem(to_integer(write_addr(bram_addr_range))) <= memory_write_data;
      end if;
    end process;

    read_memory : process
    begin
      wait until rising_edge(clk_read);

      memory_read_data <= mem(to_integer(read_addr_next(bram_addr_range)));
    end process;
  end block;

end architecture;
