#!/usr/bin/env bash
set -euo pipefail

set -a
source .env
set +a

which python
python seed.py