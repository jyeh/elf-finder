#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

exclude=(
  redis
  hello
  world
  bye
  a-very-long-workload-directory-name
)

is_excluded() {
  local name=$1 item
  for item in "${exclude[@]}"; do
    [[ $item == "$name" ]] && return 0
  done
  return 1
}

for dir in /shaking/workload/*/; do
  name=${dir%/}
  name=${name##*/}
  is_excluded "$name" && continue
  python3 xxx.py --path "${dir%/}" > "${name}.deps"
done
