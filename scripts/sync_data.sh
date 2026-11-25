#!/usr/bin/env bash
# One-way sync of raw/, config/, policy/ into FefoAgent/app/agent/data/.
# scenarios/ is never copied. The source directory is never modified.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${SYNC_DATA_DEST:-$REPO_ROOT/FefoAgent/app/agent/data}"
SUBDIRS=(raw config policy)

usage() {
  cat <<'EOF'
Usage: scripts/sync_data.sh [--from <dir>]

Copies raw/, config/ and policy/ from <dir> to FefoAgent/app/agent/data/.
scenarios/ is never copied.

Options:
  --from <dir>   Source directory (default: data/ at the repo root).
                 Relative paths resolve against the repo root.
  -h, --help     Show this message.
EOF
}

SRC="data"
while [ $# -gt 0 ]; do
  case "$1" in
    --from)
      if [ $# -lt 2 ] || [ -z "${2:-}" ] || [[ "$2" == -* ]]; then
        echo "error: --from requires a directory" >&2
        usage >&2
        exit 2
      fi
      SRC="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$SRC" in
  /*) ;;
  *) SRC="$REPO_ROOT/$SRC" ;;
esac
SRC="${SRC%/}"

if [ ! -d "$SRC" ]; then
  echo "warning: source directory not found: $SRC (destination left untouched)" >&2
  exit 0
fi

mkdir -p "$DEST"
count=0
for sub in "${SUBDIRS[@]}"; do
  if [ ! -d "$SRC/$sub" ]; then
    echo "warning: $SRC/$sub not found, skipped (destination $sub/ left untouched)" >&2
    continue
  fi
  mkdir -p "$DEST/$sub"
  # Replace contents so stale files do not linger; keep .gitkeep.
  find "$DEST/$sub" -mindepth 1 ! -name .gitkeep -delete 2>/dev/null || true
  cp -R "$SRC/$sub/." "$DEST/$sub/"
  n="$(find "$SRC/$sub" -type f | wc -l)"
  count=$((count + n))
done

echo "source:      $SRC"
echo "destination: $DEST"
echo "files copied: $count"
