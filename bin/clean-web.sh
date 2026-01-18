#!/bin/bash
ROOT_DIR="$(git rev-parse --show-toplevel)"

cd "$ROOT_DIR/bank-statements-web"
rm -rf node_modules dist
