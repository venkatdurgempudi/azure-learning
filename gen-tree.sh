#!/usr/bin/env bash

# Usage: ./tree.sh [directory]
# Default to current directory if none provided
TARGET_DIR="${1:-.}"

# Resolve to absolute path
TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd)" || {
  echo "Error: Directory not found"
  exit 1
}

cd "$TARGET_DIR" || exit 1

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
