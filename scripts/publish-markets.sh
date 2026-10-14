#!/usr/bin/env bash
# 把当前技能版本推送到各第三方技能市场。
#
# 背景：这些市场**都不会**在 GitHub 更新后自动同步。所以打版之后必须显式推一次。
# 本脚本把这一步收敛成一条命令。
#
# 用法：
#   ./scripts/publish-markets.sh                  # 全部市场
#   ./scripts/publish-markets.sh --only clawhub   # 只推一个（clawhub | lobehub）
#   ./scripts/publish-markets.sh --dry-run        # 只打印将要做什么
#   ./scripts/publish-markets.sh --changelog "自定义说明"
#
# 前置条件：
#   clawhub : clawhub whoami 有输出（npx -y clawhub@latest login，设备码授权）
#   lobehub : ~/.lobehub-market/user-credentials.json 存在（npx -y @lobehub/market-cli login）
#             CI 里不用手工准备，.github/workflows/release.yml 会先跑
#             scripts/lobehub-ci-refresh.py 用 refresh_token 换出新鲜令牌再调本脚本。
#
# 环境变量：NPX=<npx 路径>  PYTHON=<python3 路径>
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="$REPO/skills/muse-illustration"
SKILL_MD="$SKILL_DIR/SKILL.md"

SLUG="muse-illustration"
LOBEHUB_ID="stayfoool-muse-illustration"
SOURCE_REPO="https://github.com/Stayfoool/muse-illustration"
SOURCE_PATH="skills/muse-illustration"
LB_CRED="$HOME/.lobehub-market/user-credentials.json"

NPX="${NPX:-npx}"
PYTHON="${PYTHON:-python3}"
TARGETS=("clawhub" "lobehub")
DRY_RUN=0
CUSTOM_CHANGELOG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --only)
      [ -n "${2:-}" ] || { echo "--only 需要一个平台名" >&2; exit 2; }
      TARGETS=("$2"); shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --changelog)
      [ -n "${2:-}" ] || { echo "--changelog 需要一段文字" >&2; exit 2; }
      CUSTOM_CHANGELOG="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "未知参数：$1" >&2; exit 2 ;;
  esac
done

[ -f "$SKILL_MD" ] || { echo "找不到 $SKILL_MD" >&2; exit 1; }

# ── 版本号：从 SKILL.md 的 metadata.version 读（Release Please 自动维护）──
VER="$(sed -n 's/^  version: *"\{0,1\}\([0-9][0-9.]*\)"\{0,1\}.*/\1/p' "$SKILL_MD" | head -1)"
[ -n "$VER" ] || { echo "无法从 SKILL.md 解析版本号" >&2; exit 1; }

# ── 溯源信息：优先用 tag 指向的提交 ──
if git -C "$REPO" rev-parse "v$VER^{commit}" >/dev/null 2>&1; then
  SOURCE_COMMIT="$(git -C "$REPO" rev-parse "v$VER^{commit}")"
  SOURCE_REF="v$VER"
else
  SOURCE_COMMIT="$(git -C "$REPO" rev-parse HEAD)"
  SOURCE_REF="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
fi

# ── 从 CHANGELOG.md 抽当前版本的说明，去掉 markdown 链接 ──
if [ -n "$CUSTOM_CHANGELOG" ]; then
  CHANGELOG="$CUSTOM_CHANGELOG"
else
  CHANGELOG="$(awk -v ver="$VER" '
      $0 ~ "^## \\[" ver "\\]" { found=1; next }
      found && /^## \[/         { exit }
      found                     { print }
    ' "$REPO/CHANGELOG.md" \
    | sed -e 's/\[\([^]]*\)\]([^)]*)/\1/g' -e '/^[[:space:]]*$/d' \
    | head -12)"
  [ -n "$CHANGELOG" ] || CHANGELOG="版本 $VER"
fi

echo "技能      : $SLUG"
echo "版本      : $VER"
echo "溯源      : $SOURCE_REPO @ $SOURCE_REF ($SOURCE_COMMIT)"
echo "市场      : ${TARGETS[*]}"
echo "说明      : $CHANGELOG"
[ "$DRY_RUN" = "1" ] && echo "模式      : dry-run（不会真正发布）"
echo

has_target() { for t in "${TARGETS[@]}"; do [ "$t" = "$1" ] && return 0; done; return 1; }

# ── ClawHub ────────────────────────────────────────────────────────────────
if has_target clawhub; then
  echo "── ClawHub ─────────────────────────────────────────────"
  if [ "$DRY_RUN" != "1" ]; then
    WHO="$("$NPX" -y clawhub@latest whoami 2>/dev/null | tail -1 || true)"
    case "$WHO" in
      ""|*"not logged in"*|*"Not logged in"*)
        echo "  ⚠️  未登录。请先跑：npx -y clawhub@latest login" >&2; exit 1 ;;
      *) echo "  发布者：$WHO" ;;
    esac
    echo "  上传中（约 2 分钟，24 个文件）…"
    "$NPX" -y clawhub@latest --no-input skill publish "$SKILL_DIR" \
      --slug "$SLUG" \
      --version "$VER" \
      --changelog "$CHANGELOG" \
      --source-repo "$SOURCE_REPO" \
      --source-commit "$SOURCE_COMMIT" \
      --source-ref "$SOURCE_REF" \
      --source-path "$SOURCE_PATH" \
      --json
  else
    echo "  [dry-run] clawhub skill publish $SKILL_DIR --version $VER …"
  fi
  echo "  ⓘ 返回 pending-publication 是正常的，等它的扫描器跑完才成为 latest。"
  echo
fi

# ── LobeHub ────────────────────────────────────────────────────────────────
#
# 这里**故意不用官方的 `lhm skill publish`**：它的 SDK 把请求头写死成
# Content-Type: application/json，却往 body 里塞 multipart FormData，
# 服务端必然回 {"error":"Failed to parse form data"}。
# 我们的绕行方式是按同一接口用 curl 发正确的 multipart。
if has_target lobehub; then
  echo "── LobeHub ─────────────────────────────────────────────"

  if [ "$DRY_RUN" = "1" ]; then
    echo "  [dry-run] POST ${LOBEHUB_BASE_URL:-https://market.lobehub.com}/api/v1/user/skills/$LOBEHUB_ID/versions （上传 zip）"
  else
    # 凭据文件：本地由 `lhm login` 写入；CI 由 scripts/lobehub-ci-refresh.py 刷新后写入。
    [ -f "$LB_CRED" ] || {
      echo "  ⚠️  找不到凭据 $LB_CRED。" >&2
      echo "      本地：npx -y @lobehub/market-cli login" >&2
      echo "      CI  ：先跑 scripts/lobehub-ci-refresh.py（需要 LOBEHUB_REFRESH_TOKEN）" >&2
      exit 1; }

    read -r LB_TOKEN LB_BASE LB_WHO < <("$PYTHON" -c "
import json,sys
d=json.load(open(sys.argv[1]))
print(d['accessToken'], d['baseUrl'], d.get('displayName',''))
" "$LB_CRED")

    echo "  登录态：${LB_WHO:-（未记录显示名）}"
    ZIP="$(mktemp -t lobeskill.XXXXXX).zip"
    "$PYTHON" - "$SKILL_DIR" "$ZIP" <<'PY'
import os, sys, zipfile
src, out = sys.argv[1], sys.argv[2]
SKIP = {"node_modules", "__pycache__"}
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for entry in sorted(os.listdir(src)):
        if entry.startswith(".") or entry in SKIP:
            continue
        full = os.path.join(src, entry)
        if os.path.isdir(full):
            for cur, dirs, files in os.walk(full):
                dirs[:] = [d for d in sorted(dirs)
                           if not d.startswith(".") and d not in SKIP]
                for f in sorted(files):
                    if f.startswith(".") or f in SKIP:
                        continue
                    fp = os.path.join(cur, f)
                    z.write(fp, os.path.relpath(fp, src))
        else:
            z.write(full, entry)
PY
    echo "  打包：$(du -h "$ZIP" | cut -f1)（zip 为根目录结构，与官方 CLI 一致）"
    RESP="$(curl -s --noproxy '*' --max-time 300 -X POST \
      "$LB_BASE/api/v1/user/skills/$LOBEHUB_ID/versions" \
      -H "Authorization: Bearer $LB_TOKEN" \
      -F "file=@$ZIP;type=application/zip")"
    rm -f "$ZIP"
    echo "  $RESP"
  fi
  echo "  ⓘ LobeHub 的版本号是它自己按 patch 递增的，不跟随仓库 tag。"
  echo
fi

# ── skills.sh ──────────────────────────────────────────────────────────────
cat <<'EOF'
── skills.sh ───────────────────────────────────────────
  无需推送。用户执行 `npx skills add Stayfoool/muse-illustration` 时
  直接从 GitHub 取内容，装到的永远是最新版。
  目录页信息由 Vercel 的开源抓取流水线按安装遥测刷新，不受本脚本控制。
EOF
