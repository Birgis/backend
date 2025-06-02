#!/bin/bash

export PYTHONPATH=$PWD
export TEST_DATABASE_URL="sqlite://"

# Create temporary directory for coverage
TEMP_DIR=$(mktemp -d)
export COVERAGE_FILE="$TEMP_DIR/.coverage"

# Run tests with coverage
pytest tests/ --cov=. --cov-report=term-missing --no-cov-on-fail

# Clean up
rm -rf "$TEMP_DIR" 