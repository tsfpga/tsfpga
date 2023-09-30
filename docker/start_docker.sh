#!/bin/bash
# Start docker session with the tsfpga CI image.
# This a just a very crude script. Adjust as necessary.

HOSTNAME=`hostname`
USER_ID=`id -u ${USER}`

docker run \
  --rm \
  --interactive \
  --tty \
  --hostname "${HOSTNAME}" \
  --user "${USER_ID}:${USER_ID}" \
  --volume "/etc/localtime:/etc/localtime:ro" \
  --volume "${HOME}/work/repo:/repo" \
  --workdir "/repo" \
  tsfpga/ci_everything:latest \
  /bin/bash
