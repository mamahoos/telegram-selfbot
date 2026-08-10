#!/bin/sh
set -e

chown -R appuser:appuser /app/data /app/logs /app/tmp

exec gosu appuser "$@"
