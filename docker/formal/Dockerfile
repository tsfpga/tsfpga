# Use ghdl/synth:formal as base
FROM ghdl/synth:formal

# Install pip
RUN apt-get update && \
  apt-get install -y \
    python3-pip

# A subset of requirements.txt, only what is needed for formal.py
RUN python3 -m pip --no-cache-dir install \
    colorama \
    toml \
    vunit_hdl
