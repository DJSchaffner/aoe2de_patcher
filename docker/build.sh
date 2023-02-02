#!/usr/bin/env bash

CWD=$(readlink -e "$(dirname "$0")")
cd "${CWD}/.." || exit $?

DOCKER_TAG="${DOCKER_TAG:-"aoe2de_patcher"}"
GAME_DIR="${GAME_DIR:-"${HOME}/.steam/steam/steamapps/common/AoE2DE"}"

docker build -f docker/Dockerfile -t "${DOCKER_TAG}" \
	--build-arg "${GAME_DIR}" \
	--build-arg UID="${UID:-$(id -u)}" \
	--build-arg UNAME="${UNAME:-$(id -un)}" \
	--build-arg GID="${GID:-$(id -g)}" \
	. || exit $?

docker/run.sh pip freeze --find-links --all > docker/requirements-freeze.txt

docker/run.sh python3 -m nuitka \
	--enable-plugin=tk-inter \
	--include-data-dir=res=res \
	--standalone \
	--follow-imports \
	--remove-output \
	--windows-disable-console \
	src/aoe2de_patcher.py
