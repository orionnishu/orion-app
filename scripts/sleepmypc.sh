#!/usr/bin/env bash
# Backward-compatible wrapper — calls orion-node stop desktop-pc
exec "$(dirname "$0")/orion-node" stop desktop-pc