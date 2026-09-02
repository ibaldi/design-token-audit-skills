#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: ./scripts/release.sh <version>"
  echo "Example: ./scripts/release.sh v0.1.0"
  exit 1
fi

VERSION="$1"
PACKAGE_VERSION="${VERSION#v}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist/claude"

cd "$ROOT_DIR"

if ! [[ "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must use vMAJOR.MINOR.PATCH, for example v0.4.3"
  exit 1
fi

python3 ./scripts/check_release.py --version "$PACKAGE_VERSION"

./scripts/build-claude-zips.sh

gh release create "$VERSION" "$DIST_DIR"/*.zip \
  --title "$VERSION" \
  --notes "Claude skill ZIP packages for $VERSION."
