#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/export-showcase.sh /absolute/path/to/empty-directory"
  exit 2
fi

target=$1
if [ -e "$target" ] && [ "$(find "$target" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]; then
  echo "Target must not exist or must be empty: $target"
  exit 2
fi

mkdir -p "$target"
git archive HEAD | tar -x -C "$target"
printf '%s\n' "Showcase exported to $target"
printf '%s\n' "Initialize a fresh Git history there before publishing."
