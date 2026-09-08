#!/bin/bash
# Install the optional native-screensaver pacing helper for this user.
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
target="$HOME/.local/bin/ttfx"

[[ -x /usr/bin/ttfx ]] || { echo "Omarchy's /usr/bin/ttfx is required." >&2; exit 1; }
[[ -s $source_dir/scene.txt ]] || { echo "The screensaver scene is missing." >&2; exit 1; }
if [[ -e $target || -L $target ]]; then
  if cmp -s "$source_dir/ttfx" "$target"; then
    echo "Violet Oni screensaver helper is already installed."
    exit 0
  fi
  if grep -q '^# Violet Oni:' "$target" && grep -q 'engine=/usr/bin/ttfx' "$target"; then
    install -m 755 "$source_dir/ttfx" "$target"
    hash -r
    echo "Updated the Violet Oni screensaver helper: $target"
    exit 0
  fi
  echo "An existing $target was found; it has not been overwritten." >&2
  exit 1
fi

mkdir -p "$HOME/.local/bin"
install -m 755 "$source_dir/ttfx" "$target"
hash -r
resolved=$(command -v ttfx)
if [[ $(readlink -f "$resolved") != "$target" ]]; then
  echo "Installed $target, but it is not first on PATH." >&2
  echo "Put ~/.local/bin before /usr/bin in your desktop PATH to enable it." >&2
  exit 1
fi
echo "Installed the optional Violet Oni screensaver helper: $target"
echo "With Violet Oni selected, run: omarchy launch screensaver force"
