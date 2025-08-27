#!/bin/bash
# Script to run ruff check while ignoring whitespace rules W291, W292, W293

echo "Running ruff check with whitespace rules ignored..."
ruff check --select E,W --ignore W291,W292,W293 "$@"