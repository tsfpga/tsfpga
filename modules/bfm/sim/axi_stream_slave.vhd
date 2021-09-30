-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------
-- Verify data on an AXI stream interface.
-- Reference data and expected ID (optional) is pushed to a queue by the user.
--
-- The byte length of the bursts (as indicated by the length of the reference_data_queue arrays)
-- does not need to be aligned with the data width of the bus.
-- If unaligned, the last data beat will not have all byte lanes checked against reference data.
-- -------------------------------------------------------------------------------------------------

library ieee;
context ieee.ieee_std_context;

library vunit_lib;
context vunit_lib.vc_context;
context vunit_lib.vunit_context;

library bfm;


entity axi_stream_slave is
  generic (
    -- Set to zero in order to disable 'id' check. In this case, nothing has to be pushed
    -- to 'reference_id_queue'.
    id_width_bits : natural := 0;
    data_width_bits : positive;
    -- Push reference data (integer_array_t with push_ref()) to this queue.
    -- Each element should be an unsigned byte. Little endian byte order is assumed.
    -- The integer arrays will be deallocated after this BFM is done with them.
    reference_data_queue : queue_t;
    -- Push reference 'id' for each data burst to this queue. All data beats in a burst must have
    -- the same ID, and there may be no interleaving of data.
    -- If 'id_width_bits' is zero, no check will be performed and nothing shall be pushed to
    -- this queue.
    reference_id_queue : queue_t := null_queue;
    stall_config : stall_config_t := null_stall_config;
    -- Is also used for the random seed for handshaking stall.
    -- Set to something unique in order to vary the random sequence.
    logger_name_suffix : string := ""
  );
  port (
    clk : in std_logic;
    --
    ready : out std_logic := '0';
    valid : in std_logic;
    last : in std_logic;
    id : in unsigned(id_width_bits - 1 downto 0) := (others => '0');
    data : in std_logic_vector(data_width_bits - 1 downto 0);
    strb : in std_logic_vector(data_width_bits / 8 - 1 downto 0) := (others => '1')
  );
end entity;

architecture a of axi_stream_slave is

  constant bytes_per_beat : positive := data_width_bits / 8;
  signal burst_idx : natural := 0;
  signal data_is_ready : std_logic := '0';

begin

  ------------------------------------------------------------------------------
  main : process
    variable reference_id : natural;
    variable reference_data : integer_array_t := null_integer_array;
    variable burst_length_bytes, burst_length_beats : positive := 1;

    variable byte_lane_idx : natural := 0;
    variable is_last_beat : boolean := false;
  begin
    while is_empty(reference_data_queue) loop
      wait until rising_edge(clk);
    end loop;
    reference_data := pop_ref(reference_data_queue);

    burst_length_bytes := length(reference_data);
    burst_length_beats := (burst_length_bytes + bytes_per_beat - 1) / bytes_per_beat;

    data_is_ready <= '1';

    -- Pop reference ID for this burst, if applicable
    if id'length > 0 then
      check_true(not is_empty(reference_id_queue), "Must push ID at same time as data");
      reference_id := pop(reference_id_queue);
    end if;

    for byte_idx in 0 to burst_length_bytes - 1 loop
      byte_lane_idx := byte_idx mod bytes_per_beat;
      is_last_beat := byte_idx / bytes_per_beat = burst_length_beats - 1;

      if byte_lane_idx = 0 then
        wait until (ready and valid) = '1' and rising_edge(clk);
        check_equal(
          last,
          is_last_beat,
          "'last' check at burst_idx=" & to_string(burst_idx) & ",byte_idx=" & to_string(byte_idx)
        );
      end if;

      check_equal(
        strb(byte_lane_idx),
        '1',
        "'strb' check at burst_idx=" & to_string(burst_idx) & ",byte_idx=" & to_string(byte_idx)
      );
      check_equal(
        unsigned(data((byte_lane_idx + 1) * 8 - 1 downto byte_lane_idx * 8)),
        get(arr=>reference_data, idx=>byte_idx),
        "'data' check at burst_idx=" & to_string(burst_idx) & ",byte_idx=" & to_string(byte_idx)
      );

      if id'length > 0 then
        check_equal(
          unsigned(id),
          reference_id,
          "'id' check at burst_idx=" & to_string(burst_idx) & ",byte_idx=" & to_string(byte_idx)
        );
      end if;
    end loop;

    -- Check strobe for last data beat. If burst length aligns with the bus width, all lanes will
    -- have been checked as '1' above. If burst is not aligned, one or more byte lanes at the top
    -- shall be strobed out.
    for byte_idx in byte_lane_idx + 1 to bytes_per_beat - 1 loop
      check_equal(
        strb(byte_idx),
        '0',
        "'strb' check at burst_idx=" & to_string(burst_idx) & ",byte_idx=" & to_string(byte_idx)
      );
    end loop;

    -- Deallocate after we are done with the data.
    deallocate(reference_data);

    -- Default: Signal "not ready" to handshake BFM before next packet.
    -- If queue is not empty, it will instantly be raised again (no bubble cycle).
    data_is_ready <= '0';

    burst_idx <= burst_idx + 1;
  end process;


  ------------------------------------------------------------------------------
  handshake_slave_int : entity bfm.handshake_slave
    generic map(
      stall_config => stall_config,
      logger_name_suffix => logger_name_suffix,
      data_width => data'length,
      id_width => id'length
    )
    port map(
      clk => clk,
      --
      data_is_ready => data_is_ready,
      --
      ready => ready,
      valid => valid,
      last => last,
      id => id,
      data => data,
      strobe => strb
    );

end architecture;
