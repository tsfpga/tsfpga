Docker image for formal checks
==============================

There is a docker image available that is used for gitlab CI
The image is available in the ``tsfpga`` organization: https://hub.docker.com/repository/docker/tsfpga/formal

Dockerhub can't retreive data from gitlab repositories and so cannot build the image automatically.
Instead it needs to be built locally upon updates, and then pushed to dockerhub.

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

Build the image by running

```
docker build -t tsfpga/formal docker/formal
```

from the repository root.

Run
---

Run the image locally using e.g.:

```
docker run --interactive --tty --rm --volume ~/work/repo:/repo --workdir /repo/tsfpga tsfpga/formal /bin/bash
```

Push
----

Pushing an updated ``Dockerfile`` to dockerhub is done with:

```
docker login
docker push tsfpga/formal
```

Note that you need a dockerhub user ID, and that your user needs to be part of the ``tsfpga`` organization.
