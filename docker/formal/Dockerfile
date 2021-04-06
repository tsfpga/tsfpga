# Use ghdl/synth:formal as base
FROM ghdl/synth:formal

# Install pip
RUN apt-get update && \
  apt-get install -y python3-pip && \
  # A subset of requirements.txt, only what is needed for formal.py
  python3 -m pip --no-cache-dir install \
    colorama \
    tomlkit \
    vunit_hdl  && \
  # Remove pip and all its dependencies again
  apt-get purge -y --auto-remove python3-pip && \
  # Remove files left over by "pip install" run
  rm -rf ~/.cache
