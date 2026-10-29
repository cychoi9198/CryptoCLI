#!/usr/bin/env bash
# crypto-cli Hermes 스킬 설치 (Linux / macOS)
# 사용: ./install.sh [--force] [--dest DIR]
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/skills/crypto/crypto-cli"
DEST="${HERMES_HOME:-$HOME/.hermes}/skills/crypto/crypto-cli"
FORCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --force) FORCE=1 ;;
    --dest)  DEST="$2"; shift ;;
    *) echo "알 수 없는 옵션: $1" >&2; exit 2 ;;
  esac
  shift
done

PY="$(command -v python3 || command -v python || true)"
[ -n "$PY" ] || { echo "[ERROR] python3 를 찾을 수 없습니다." >&2; exit 1; }

if ! "$PY" -c "import cryptography" 2>/dev/null; then
  echo "[INFO] cryptography 설치 중..."
  "$PY" -m pip install -r "$(dirname "$SRC")/../../requirements.txt" \
    || "$PY" -m pip install --user -r "$(dirname "$SRC")/../../requirements.txt"
fi

if [ -e "$DEST" ]; then
  if [ "$FORCE" -eq 1 ]; then rm -rf "$DEST"
  else echo "[ERROR] 이미 존재: $DEST (덮어쓰려면 --force)" >&2; exit 1; fi
fi
mkdir -p "$(dirname "$DEST")"
cp -r "$SRC" "$DEST"
chmod +x "$DEST/scripts/"*.py
echo "[OK] 설치: $DEST"

"$PY" "$DEST/scripts/selftest.py" | tail -1
echo "새 Hermes 세션에서 스킬이 활성화됩니다."
