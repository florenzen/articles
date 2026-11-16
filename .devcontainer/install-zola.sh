#!/bin/sh
# Install Zola from the pkg.haus APT archive (https://pkg.haus), as recommended by
# https://www.getzola.org/documentation/getting-started/installation/#debian
#
# Used by .devcontainer/Dockerfile and the GitHub workflows, so the Zola version is set only here.
# Must run as root on Debian 13 (trixie).
set -eu

ZOLA_VERSION="0.23.6"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends ca-certificates curl

curl -fsSL -o /usr/share/keyrings/pkghaus-archive-keyring.gpg \
    https://apt.pkg.haus/pkghaus-archive-keyring.gpg

cat > /etc/apt/sources.list.d/pkghaus.sources << SOURCES
Types: deb
URIs: https://apt.pkg.haus
Suites: trixie
Components: main
Signed-By: /usr/share/keyrings/pkghaus-archive-keyring.gpg
SOURCES

apt-get update
apt-get install -y --no-install-recommends pkghaus-archive-keyring "zola=${ZOLA_VERSION}-*"
rm -rf /var/lib/apt/lists/*

zola --version
