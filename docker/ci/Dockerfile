# Use base image from the GHDL project which includes GHDL and VUnit.
# Use the master image since we need some of the VUnit updates since latest release.
# The release image is smaller however, so we can switch to that when VUnit makes a new release.
# Note that the mcode image is much smaller than the gcc image.
FROM ghdl/vunit:mcode-master AS ci_py_sim

LABEL description="Includes everything that is needed for CI simulation/pytest of the tsfpga project(s)."

RUN apt-get update && \
  apt-get install --yes --no-install-recommends \
  git \
  g++

RUN python3 -m pip --no-cache-dir install --upgrade \
  # Older version since there is an issue with symbolator setup.py using _use_2to3:
  # https://stackoverflow.com/questions/69100275/error-while-downloading-the-requirements-using-pip-install-setup-command-use-2
  "setuptools<58" \
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
  # Older version since symbolator_sphinx does not work with newer:
  # "exception: cannot import name 'ENOENT'"
  sphinx==3.5.4 \
  sphinx-rtd-theme \
  sphinx_sitemap \
  sphinxcontrib-wavedrom \
  symbolator && \
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
