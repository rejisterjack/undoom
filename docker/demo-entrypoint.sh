#!/bin/sh
# Capture the order-lookup failure, replay the fix, and run the suite.
set -eu
mkdir -p /work
cd /app
export UNDOOM_DEMO_ROOT=/work
python /app/examples/order_lookup/demo.py
cd /work
python -m undoom test --format text
echo "case files:"
find /work/.undoom/cases -type f
