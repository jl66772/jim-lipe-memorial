#!/usr/bin/env bash
# Rebuild the site from the Kululu source folder and push any changes to GitHub Pages.
set -euo pipefail
cd "$(dirname "$0")"
python3 build.py
git add -A
if git diff --cached --quiet; then echo "No changes to publish."; exit 0; fi
git commit -q -m "Update site $(date +%Y-%m-%d)"
git push -q origin main
echo "Published: https://jl66772.github.io/jim-lipe-memorial/"
