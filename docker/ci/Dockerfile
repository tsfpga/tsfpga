# Use base image from the GHDL project which includes GHDL and VUnit.
# Note that the mcode image is much smaller than the gcc image.
FROM ghdl/vunit:mcode AS ci_py_sim

LABEL description="Includes everything that is needed for CI simulation/pytest of the tsfpga project(s)."

RUN apt-get update && \
  apt-get install --yes --no-install-recommends \
  git \
  g++

RUN python3 -m pip --no-cache-dir install --upgrade \
  black \
  GitPython \
  flake8 \
  pylint \
  pytest \
  pytest-cov \
  tomlkit && \
  rm -rf ~/.cache


FROM ci_py_sim AS ci_py_sim_sphinx

LABEL description="Further includes everything that is needed for building sphinx documentation of the tsfpga project(s)."

RUN apt-get install --yes --no-install-recommends \
  # Needed by symbolator/wavedrom/dot
  gir1.2-gtk-3.0 \
  graphviz \
  libgirepository1.0-dev \
  libcairo2-dev \
  pkg-config \
  python3-dev

RUN python3 -m pip --no-cache-dir install \
  pybadges \
  pycairo \
  PyGObject \
  sphinx \
  sphinx-rtd-theme \
  sphinx_sitemap \
  sphinxcontrib-wavedrom \
  # Install symbolator and hdlparse from github forks that are maintained.
  # The official version do not work with newer setuptools or newer sphinx.
  # The pyHDLParser repo seems to be under active development and the current master did not
  # work, so peg to the latest revision that does work for us.
  git+https://github.com/hdl/pyHDLParser@354dc73a231677f277709633b9bcd0110f1816d0 \
  git+https://github.com/hdl/symbolator && \
  rm -rf ~/.cache


FROM ci_py_sim_sphinx AS ci_everything

LABEL description="Further includes everything that is needed for signal processing analysis."

RUN apt-get install --yes --no-install-recommends \
  # Needed to package artifacts
  zip

RUN python3 -m pip --no-cache-dir install \
  matplotlib \
  scipy && \
  rm -rf ~/.cache
