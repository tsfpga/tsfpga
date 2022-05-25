Docker images for CI
====================

There is a set of images defined in ``ci/`` that are used for CI (pytest, simulate, build sphinx).
That Dockerfile has one stage that includes everything needed for pytest and GHDL/VUnit simulation.
On top of that is another stage that adds everything needed to build sphinx documentation.

Note that the images are used for CI of sister projects as well (``hdl_modules``).

The images are available in the ``tsfpga`` organization on dockerhub:

* https://hub.docker.com/repository/docker/tsfpga/ci_py_sim
* https://hub.docker.com/repository/docker/tsfpga/ci_py_sim_sphinx
* https://hub.docker.com/repository/docker/tsfpga/ci_everything

Unfortunately we can not use automated dockerhub builds since this project is sponsored by a
commercial company.
Details:

* https://docs.docker.com/docker-hub/builds/
* https://www.docker.com/community/open-source/application

Instead we need to build the images locally upon updates, and then push to dockerhub.


Install docker
--------------

Install docker with:

```
sudo apt install docker.io
```

Note that you should not use the snap package.

Add to group:

```
sudo usermod -a -G docker $USER
exec su -l $USER
```


Build
-----

Build the images by running the script

```
./docker/build_docker_images.sh
```

from the repository root.


Run
---

Run an image locally using the ``docker/start_docker.sh`` script.


Push
----

Pushing an updated ``Dockerfile`` to dockerhub is done with:

```
docker login
docker push tsfpga/ci_py_sim
docker push tsfpga/ci_py_sim_sphinx
docker push tsfpga/ci_everything
```

Note that you need a dockerhub user ID, and that your user needs to be part of the
``tsfpga`` organization.
