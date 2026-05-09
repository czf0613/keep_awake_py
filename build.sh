#!/bin/bash
set -e
cd "$(dirname "$0")"

rm -rf dist || true
rm -rf build || true
rm -rf src/keep_awake.egg-info || true

uv sync
uv build
