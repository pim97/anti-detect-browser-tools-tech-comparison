#!/usr/bin/env bash
# Clone + inspect the anti-detect tool sources inside a hardened Docker container.
#
# The trees are unaudited third-party code, so they never touch a host filesystem:
# they live in a Docker *volume*, cloned by a container with no capabilities and a
# read-only root, and the network is severed once the fetch completes.
#
#   ./sandbox.sh up       build image, start container, clone, then cut network
#   ./sandbox.sh refresh  reconnect, git fetch, cut network again
#   ./sandbox.sh sh       interactive shell inside the sandbox (offline)
#   ./sandbox.sh down     destroy container (volume survives)
#   ./sandbox.sh nuke     destroy container AND volume
set -uo pipefail

VOL=antidetect-src
CTR=antidetect-box
IMG=antidetect-inspect:latest
REPOS="
daijro/camoufox
daijro/browserforge
Kaliiiiiiiiii-Vinyzu/patchright
Kaliiiiiiiiii-Vinyzu/patchright-python
Kaliiiiiiiiii-Vinyzu/patchright-nodejs
Kaliiiiiiiiii-Vinyzu/CDP-Patches
DevEnterpriseSoftware/patchright-dotnet
seleniumbase/SeleniumBase
omkarcloud/botasaurus
omkarcloud/botasaurus-driver
arjun-sha/XDriver
CloakHQ/CloakBrowser
pim97/cloakbrowser-analyze
D4Vinci/Scrapling
h4ckf0r0day/obscura
h4ckf0r0day/obscura-benchmark
clearcotelabs/clearcote-browser
clearcotelabs/clearcote-profiles
rebrowser/rebrowser-patches
"

build_image() {
  docker image inspect "$IMG" >/dev/null 2>&1 && return 0
  echo "building $IMG"
  docker build -q -t "$IMG" - << "DOCKERFILE"
FROM alpine:3.20
RUN apk add --no-cache git ripgrep python3 jq file
ENV HOME=/tmp
WORKDIR /src
DOCKERFILE
}

start_ctr() {
  docker rm -f "$CTR" >/dev/null 2>&1
  docker volume create "$VOL" >/dev/null
  docker run -d --name "$CTR" \
    --cap-drop=ALL \
    --security-opt=no-new-privileges \
    --read-only --tmpfs /tmp:rw,exec,size=512m \
    --memory=4g --pids-limit=1024 \
    -e HOME=/tmp \
    -v "$VOL":/src \
    -w /src \
    "$IMG" sleep infinity >/dev/null
}

net_off() { docker network disconnect bridge "$CTR" 2>/dev/null && echo "network: DISCONNECTED"; }
net_on()  { docker network connect bridge "$CTR" 2>/dev/null && echo "network: connected"; }

do_clone() {
  for r in $REPOS; do
    name="${r#*/}"
    if docker exec "$CTR" test -d "/src/$name/.git"; then
      docker exec "$CTR" git -C "/src/$name" fetch --depth 50 -q origin >/dev/null 2>&1 \
        && docker exec "$CTR" sh -c "cd /src/$name && git reset --hard -q \"origin/\$(git symbolic-ref --short HEAD)\"" >/dev/null 2>&1 \
        && echo "  pulled  $r" || echo "  FAIL    $r"
    else
      docker exec "$CTR" git clone --depth 50 -q "https://github.com/$r.git" "/src/$name" >/dev/null 2>&1 \
        && echo "  cloned  $r" || echo "  FAIL    $r"
    fi
  done
}

case "${1:-up}" in
  up)      build_image; start_ctr; net_on >/dev/null; do_clone; net_off ;;
  refresh) net_on >/dev/null; do_clone; net_off ;;
  sh)      docker exec -it "$CTR" sh ;;
  down)    docker rm -f "$CTR" >/dev/null 2>&1 && echo "container removed" ;;
  nuke)    docker rm -f "$CTR" >/dev/null 2>&1; docker volume rm "$VOL" >/dev/null 2>&1 && echo "container + volume removed" ;;
  *)       echo "usage: $0 {up|refresh|sh|down|nuke}"; exit 1 ;;
esac
