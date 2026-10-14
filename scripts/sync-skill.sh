#!/usr/bin/env bash
# 把本地安装的技能同步进本仓库（一处开发、一处分发）
# 用法：./scripts/sync-skill.sh [源目录]
# 默认源目录：$HOME/.workbuddy/skills/muse-illustration
set -euo pipefail

SRC="${1:-$HOME/.workbuddy/skills/muse-illustration}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/skills/muse-illustration"

if [ ! -d "$SRC" ]; then
  echo "源目录不存在：$SRC" >&2
  exit 1
fi

mkdir -p "$DEST"
rsync -a --delete --exclude '.DS_Store' "$SRC/" "$DEST/"
echo "已同步：$SRC  ->  $DEST"
