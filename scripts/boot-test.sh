#!/usr/bin/env bash
# Installs the pack as a dedicated server the same way the Pelican server does (NeoForge installer,
# then packwiz-installer in server mode) and boots it until "Done". Exits non-zero on a crash or
# timeout, so a broken mod update fails CI instead of the live server.
#
# Usage: scripts/boot-test.sh <server-dir> <pack.toml URL>
# Needs: java 21, curl. Extra JVM flags via BOOT_TEST_JAVA_OPTS (default -Xmx6G).
set -euo pipefail

SERVER_DIR=$1
PACK_URL=$2
TIMEOUT_SECS=${BOOT_TEST_TIMEOUT:-1200}
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)

NEOFORGE=$(sed -n 's/^neoforge = "\(.*\)"/\1/p' "$REPO_ROOT/pack.toml")
# shellcheck source=tools.env
source "$REPO_ROOT/scripts/tools.env"

mkdir -p "$SERVER_DIR"
cd "$SERVER_DIR"

fetch() { # url dest sha256
  [[ -f $2 ]] && echo "$3  $2" | sha256sum -c --quiet 2>/dev/null && return 0
  curl -fsSL -o "$2" "$1"
  echo "$3  $2" | sha256sum -c --quiet
}
fetch "$BOOTSTRAP_URL" packwiz-installer-bootstrap.jar "$BOOTSTRAP_SHA256"
fetch "$INSTALLER_URL" packwiz-installer.jar "$INSTALLER_SHA256"

if [[ ! -f libraries/net/neoforged/neoforge/$NEOFORGE/unix_args.txt ]]; then
  echo "Installing NeoForge $NEOFORGE server"
  curl -fsSL -o neoforge-installer.jar \
    "https://maven.neoforged.net/releases/net/neoforged/neoforge/$NEOFORGE/neoforge-$NEOFORGE-installer.jar"
  java -jar neoforge-installer.jar --installServer >neoforge-install.log 2>&1 || { tail -20 neoforge-install.log; exit 1; }
  rm -f neoforge-installer.jar neoforge-installer.jar.log
fi

echo "Syncing pack from $PACK_URL"
java -jar packwiz-installer-bootstrap.jar --bootstrap-no-update --bootstrap-main-jar packwiz-installer.jar \
  -g -s server "$PACK_URL"

echo "eula=true" >eula.txt
# Offline mode so a local test client can join; the real server keeps online-mode=true.
[[ -f server.properties ]] || printf 'online-mode=false\nlevel-seed=emberandiron\nspawn-protection=0\nallow-flight=true\n' >server.properties

rm -f logs/latest.log
mkfifo console.in 2>/dev/null || true
# Hold the fifo open so the server never sees EOF on stdin while we wait.
exec 3<>console.in
# shellcheck disable=SC2086
java ${BOOT_TEST_JAVA_OPTS:--Xmx6G} @libraries/net/neoforged/neoforge/"$NEOFORGE"/unix_args.txt nogui <console.in >server.out 2>&1 &
PID=$!

START=$SECONDS
while kill -0 "$PID" 2>/dev/null; do
  if grep -qE 'Done \([0-9.]+s\)! For help' server.out; then
    echo "Server reached Done after $((SECONDS - START))s"
    grep -oE 'Done \([0-9.]+s\)' server.out
    if [[ -n ${BOOT_TEST_HOLD:-} ]]; then
      echo "Holding the server open until $SERVER_DIR/stop-now exists"
      while [[ ! -f stop-now ]] && kill -0 "$PID" 2>/dev/null; do sleep 2; done
      rm -f stop-now
    fi
    echo stop >&3
    wait "$PID" || true
    exec 3>&-
    exit 0
  fi
  if (( SECONDS - START > TIMEOUT_SECS )); then
    echo "Timed out after ${TIMEOUT_SECS}s"; kill "$PID"; tail -60 server.out; exit 1
  fi
  sleep 3
done
wait "$PID" && rc=0 || rc=$?
echo "Server exited (code $rc) before reaching Done"
tail -80 server.out
ls crash-reports 2>/dev/null && sed -n '1,60p' "$(ls -t crash-reports/* | head -1)"
exit 1
