#!/bin/sh
set -e

chown -R appuser:appuser /app/data /app/logs /app/tmp /app/volumes/sessions

exec gosu appuser "$@"
