#!/usr/bin/env bash
# Builds the Prism Launcher instance zip players import. The instance syncs the pack from GitHub
# before every launch, so this zip only needs rebuilding when the tooling or launch settings change.
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck source=tools.env
source "$REPO_ROOT/scripts/tools.env"
NEOFORGE=$(sed -n 's/^neoforge = "\(.*\)"/\1/p' "$REPO_ROOT/pack.toml")

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/Ember & Iron/minecraft"
cp "$REPO_ROOT/prism/instance.cfg" "$STAGE/Ember & Iron/"
cat >"$STAGE/Ember & Iron/mmc-pack.json" <<JSON
{
    "components": [
        { "important": true, "uid": "net.minecraft", "version": "1.21.1" },
        { "uid": "net.neoforged", "version": "$NEOFORGE" }
    ],
    "formatVersion": 1
}
JSON
curl -fsSL -o "$STAGE/Ember & Iron/minecraft/packwiz-installer-bootstrap.jar" "$BOOTSTRAP_URL"
curl -fsSL -o "$STAGE/Ember & Iron/minecraft/packwiz-installer.jar" "$INSTALLER_URL"
(cd "$STAGE/Ember & Iron/minecraft" && echo "$BOOTSTRAP_SHA256  packwiz-installer-bootstrap.jar
$INSTALLER_SHA256  packwiz-installer.jar" | sha256sum -c --quiet)

mkdir -p "$REPO_ROOT/build"
rm -f "$REPO_ROOT/build/Ember-and-Iron-Prism.zip"
(cd "$STAGE" && zip -qr "$REPO_ROOT/build/Ember-and-Iron-Prism.zip" "Ember & Iron")
echo "Built build/Ember-and-Iron-Prism.zip (NeoForge $NEOFORGE)"
