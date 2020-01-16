-- -----------------------------------------------------------------------------
-- Copyright (c) Lukas Vik. All rights reserved.
-- -----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library reg_file;
use reg_file.reg_file_pkg.all;


entity interrupt_register is
  port (
    clk : in std_logic;

    sources : in reg_t := (others => '0');
    mask : in reg_t := (others => '1');
    clear : in reg_t := (others => '0');

    status : out reg_t := (others => '0');
    trigger : out std_logic := '0'
  );
end entity;

architecture a of interrupt_register is
begin

  trigger <= or (status and mask);

  main : process
  begin
    wait until rising_edge(clk);

    for idx in sources'range loop
      if clear(idx) then
        status(idx) <= '0';
      elsif sources(idx) then
        status(idx) <= '1';
      end if;
    end loop;
  end process;

end architecture;
