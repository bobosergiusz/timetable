#!/bin/bash
set -e

sleep 3 && init_db

exec "$@"