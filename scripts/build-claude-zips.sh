#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT_DIR/skills/claude"
DIST_DIR="$ROOT_DIR/dist/claude"

python3 "$ROOT_DIR/scripts/check_release.py"

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

for skill_dir in "$SKILLS_DIR"/*; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  (
    cd "$SKILLS_DIR"
    python3 -m zipfile -c "$DIST_DIR/$skill_name.zip" "$skill_name"
  )
  echo "Built $DIST_DIR/$skill_name.zip"
done

python3 "$ROOT_DIR/scripts/check_release.py" --dist
