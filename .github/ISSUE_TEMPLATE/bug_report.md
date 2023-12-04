---
name: Bug report
about: Create a report to help us improve
title: ''
labels: Bug
assignees: ''

---

**Description**
A clear and concise description of what the issue is about.


**Expected behavior**
What you expected to happen, and what is happening instead.


**How to reproduce?**
Tell us how to reproduce this issue.
Please provide a Minimal Working Example (MWE) that triggers the issue.
With sample code it's easier to reproduce and much faster to fix.

Add code for example like this:

```python
from tsfpga.module import get_modules

modules = get_modules(None])
```

```vhdl
architecture a of ent_name is
  signal slv : std_ulogic_vector(6 downto 0) := (others => '0');
begin
  slv <= to_slv(regs_down.config.increment);
end architecture;
```

```tcl
create_ip -vlnv xilinx.com:ip:fifo_generator:13.2 -module_name fifo_generator_0
```


**Context**
Please provide the following information:

- Operating system: [e.g. Ubuntu 22.04]
- Python version: [e.g. 3.11]
- tsfpgaorigin:
  - [ ] Released package.
  - [ ] Git repository.
- tsfpga version: [e.g. 4.1.0, or git commit SHA]
- Any other relevant tool versions:
  - [e.g. FPGA build tool, simulator, etc.]


**Additional context**
Add any other context about the problem here.
If applicable, add screenshots to help explain your problem.
