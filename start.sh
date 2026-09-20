#!/usr/bin/env bash
set -e

# Run migrations once as a release step, not once per worker or replica.
exec python scripts/serve.py
