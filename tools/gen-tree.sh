#!/usr/bin/env bash

# Move to repo root (directory of this script → one level up)
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR" || exit 1

# Generate GitHub-style tree with files, excluding .git
find . ! -path "./.git*" | sort | awk '
BEGIN { FS="/" }
{
  if ($0 == ".") next
  depth = NF - 1
  indent = ""
  for (i = 1; i < depth; i++) indent = indent "│   "
  print indent "├── " $NF
}'
