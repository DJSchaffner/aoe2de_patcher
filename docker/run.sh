#!/usr/bin/env bash

CWD=$(readlink -e "$(dirname "$0")")
cd $CWD/.. || exit $?
WORKSPACE="$(pwd)"

DOCKER_TAG="${DOCKER_TAG:-"aoe2de_patcher"}"
GAME_DIR="${GAME_DIR:-"${HOME}/.steam/steam/steamapps/common/AoE2DE"}"

xhost +

docker run \
    -v "${WORKSPACE}:/opt/aoe2de_patcher" \
    -v "${GAME_DIR}:/opt/AoE2DE" \
    -v "/var/run/docker.sock:/var/run/docker.sock" \
    -v "$HOME/.Xauthority:/root/.Xauthority:rw" \
    -e DISPLAY=":0" \
    -u "${UID:-$(id -u)}:${GID:-$(id -g)}" \
    -w "/opt/aoe2de_patcher" \
    --net=host \
    --rm \
    -it \
    "${DOCKER_TAG}" \
    "$@" || exit $?
