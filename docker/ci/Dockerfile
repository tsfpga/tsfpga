# Use base image from the GHDL project which includes GHDL and VUnit.
# Note that the mcode image is much smaller than the gcc image.
# We are on "master" image until VUnit 5.0 is released, due to these issues:
# https://github.com/VUnit/vunit/issues/559
# https://github.com/VUnit/vunit/issues/777
# https://github.com/VUnit/vunit/pull/799
# https://github.com/VUnit/vunit/pull/802
# When 5.0 is relased we might change back to the release image, which is probably more stable.
# Historically the release image was smaller than the "master" image, but that does not seem to
# be the case anymore (2023-02-27).
FROM ghdl/vunit:mcode-master AS ci_py_sim

LABEL description="Includes everything that is needed for CI simulation/pytest of the tsfpga project(s)."

RUN apt-get update && \
  apt-get install --yes --no-install-recommends \
  git \
  # Functional tests in hdl_registers uses GCC to compile
  g++ \
  # So that repos/submodules can be checked out with SSH
  openssh-client \
  # Cleanup
  && apt-get autoremove --yes \
  && apt-get clean autoclean \
  && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip --no-cache-dir install --upgrade \
  # Update to latest pip before installing others
  pip \
  && python3 -m pip --no-cache-dir install --upgrade \
  black \
  GitPython \
  flake8 \
  pylint \
  pytest \
  pytest-cov \
  tomli \
  tomlkit \
  # Cleanup
  && rm -rf ~/.cache


FROM ci_py_sim AS ci_py_sim_sphinx

LABEL description="Further includes everything that is needed for building sphinx documentation of the tsfpga project(s)."

RUN apt-get update && \
  apt-get install --yes --no-install-recommends \
  # Needed by symbolator/wavedrom/dot
  gir1.2-gtk-3.0 \
  graphviz \
  libgirepository1.0-dev \
  libcairo2-dev \
  pkg-config \
  python3-dev \
  # Cleanup
  && apt-get autoremove --yes \
  && apt-get clean autoclean \
  && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip --no-cache-dir install --upgrade \
  pybadges \
  pycairo \
  PyGObject \
  sphinx \
  sphinx-rtd-theme \
  sphinx_sitemap \
  sphinxcontrib-wavedrom \
  # Install symbolator and hdlparse from github forks that are maintained.
  # The official versions do not work with newer setuptools or newer sphinx.
  # The pyHDLParser repo seems to be under active development and the current master did not
  # work, so peg to the latest revision that does work for us.
  git+https://github.com/hdl/pyHDLParser@354dc73a231677f277709633b9bcd0110f1816d0 \
  git+https://github.com/hdl/symbolator \
  # Cleanup
  && rm -rf ~/.cache


FROM ci_py_sim_sphinx AS ci_everything

LABEL description="Further includes everything that is needed for signal processing analysis."

RUN apt-get update && \
  apt-get install --yes --no-install-recommends \
  # Needed to package artifacts
  zip \
  # Cleanup
  && apt-get autoremove --yes \
  && apt-get clean autoclean \
  && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip --no-cache-dir install --upgrade \
  matplotlib \
  scipy \
  # Cleanup
  && rm -rf ~/.cache
