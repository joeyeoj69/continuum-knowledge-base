#!/usr/bin/env bash
set -euo pipefail

git diff --exit-code -- site

untracked=()
while IFS= read -r -d '' path; do
  untracked+=("$path")
done < <(git ls-files --others -z -- site)

if (( ${#untracked[@]} )); then
  printf 'untracked generated site files would enter the Pages artifact:\n' >&2
  printf '  %s\n' "${untracked[@]}" >&2
  exit 1
fi
