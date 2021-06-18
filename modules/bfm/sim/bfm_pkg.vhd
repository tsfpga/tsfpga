-- -------------------------------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
--
-- This file is part of the tsfpga project.
-- https://tsfpga.com
-- https://gitlab.com/tsfpga/tsfpga
-- -------------------------------------------------------------------------------------------------

library ieee;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vc_context;
context vunit_lib.vunit_context;


package bfm_pkg is

  -- Convenience method for getting vectors of BFM/VC elements.
  -- When doing e.g.
  --   constant my_masters : axi_stream_master_vec_t(0 to 1) :=
  --     (others => new_axi_stream_master(...));
  -- works well in some simulators (GHDL), meaning that the function is evaluated once for each
  -- element of the vector. In e.g. modelsim the function is only evaluated once, and all elements
  -- get the same value. Hence the need for this function.

  impure function get_new_queues(count : positive) return queue_vec_t;

  type memory_vec_t is array (integer range <>) of memory_t;
  impure function get_new_memories(count : positive) return memory_vec_t;

  type axi_slave_vec_t is array (integer range <>) of axi_slave_t;

  type axi_stream_master_vec_t is array (integer range <>) of axi_stream_master_t;
  impure function get_new_axi_stream_masters(
    count : positive;
    data_width : positive;
    logger_name : string;
    stall_config : stall_config_t
  ) return axi_stream_master_vec_t;

  type axi_stream_slave_vec_t is array (integer range <>) of axi_stream_slave_t;
  impure function get_new_axi_stream_slaves(
    count : positive;
    data_width : positive;
    logger_name : string;
    stall_config : stall_config_t
  ) return axi_stream_slave_vec_t;

end package;

package body bfm_pkg is

  impure function get_new_queues(count : positive) return queue_vec_t is
    variable result : queue_vec_t(0 to count - 1) := (others => null_queue);
  begin
    for queue_idx in result'range loop
      result(queue_idx) := new_queue;
    end loop;
    return result;
  end function;

  impure function get_new_memories(count : positive) return memory_vec_t is
    variable result : memory_vec_t(0 to count - 1) := (others => null_memory);
  begin
    for memory_idx in result'range loop
      result(memory_idx) := new_memory;
    end loop;
    return result;
  end function;

  impure function get_new_axi_stream_masters(
    count : positive;
    data_width : positive;
    logger_name : string;
    stall_config : stall_config_t
  ) return axi_stream_master_vec_t is
    variable result : axi_stream_master_vec_t(0 to count - 1) := (others => null_axi_stream_master);
  begin
    for result_idx in result'range loop
      result(result_idx) := new_axi_stream_master(
        data_length => data_width,
        protocol_checker => new_axi_stream_protocol_checker(
          logger => get_logger(logger_name),
          data_length => data_width
        ),
        stall_config => stall_config
      );
    end loop;
    return result;
  end function;

  impure function get_new_axi_stream_slaves(
    count : positive;
    data_width : positive;
    logger_name : string;
    stall_config : stall_config_t
  ) return axi_stream_slave_vec_t is
    variable result : axi_stream_slave_vec_t(0 to count - 1) := (others => null_axi_stream_slave);
  begin
    for result_idx in result'range loop
      result(result_idx) := new_axi_stream_slave(
        data_length => data_width,
        protocol_checker => new_axi_stream_protocol_checker(
          logger => get_logger(logger_name),
          data_length => data_width
        ),
        stall_config => stall_config
      );
    end loop;
    return result;
  end function;

end package body;
