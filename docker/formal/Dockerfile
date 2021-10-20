# Use ghdl/synth:formal as base
FROM ghdl/synth:formal

LABEL description="Includes everything that is needed to run formal verification with the tsfpga tools."

# Install pip
RUN apt-get update && \
  apt-get install --yes --no-install-recommends python3-pip && \
  # A subset of requirements.txt, only what is needed for formal.py
  python3 -m pip --no-cache-dir install \
  colorama \
  tomlkit \
  vunit_hdl  && \
  # Remove pip and all its dependencies again
  apt-get purge --yes --auto-remove python3-pip && \
  # Remove files left over by "pip install" run
  rm -rf ~/.cache
