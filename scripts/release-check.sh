#!/usr/bin/env bash
set -euo pipefail

python -m unittest discover -s tests -p 'test_*.py' -v

if [[ -f "flake.nix" ]]; then
  nix flake check
  nix fmt
fi
