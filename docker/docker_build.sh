docker build --target ci_py_sim --tag tsfpga/ci_py_sim docker/ci

docker build --target ci_py_sim_sphinx --tag tsfpga/ci_py_sim_sphinx docker/ci

docker build --tag tsfpga/formal docker/formal
