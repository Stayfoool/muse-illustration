#!/usr/bin/env bash
# 自动审查 release-please 开出的「发版申请单」，决定是否放行自动合并。
#
# 为什么需要一个"审查"环节：release-please 的申请单由机器人自己创建，
# 一旦无条件自动合并，就等于"机器人说什么就是什么"。这个脚本是合并前的**唯一把关点**，
# 它保证机器人的单子只能做它该做的事。
#
# 审查四项：
#   1. 单子必须是 release-please 开的（分支名前缀 release-please--），别的 PR 一律不放行
#   2. 它**只能**动「版本号 / CHANGELOG / manifest」这几个文件；夹带任何其它改动就拒绝
#      —— 这一条是真正有价值的部分：防止发版单里混进代码改动
#      （version.txt 属于 release-please `simple` 策略的版本存储文件，必须放行）
#   3. 版本号必须是合法 semver，且严格大于 .release-please-manifest.json 里记录的当前版本
#   4. 把变更说明打到日志里（审计留痕，事后可查"当时到底发了什么"）
#
# 输出到 $GITHUB_OUTPUT：
#   approved=true|false   是否放行
#   pr_number=<编号>
#   version=<x.y.z>
#
# 退出码：0 = 已给出结论（含"无单可审"）；1 = 审查不通过，需要人看（会让 CI 变红，这是故意的）
set -euo pipefail

ALLOWED_RE='^(version\.txt|CHANGELOG\.md|\.release-please-manifest\.json|\.claude-plugin/plugin\.json|\.claude-plugin/marketplace\.json|skills/muse-illustration/SKILL\.md)$'
BRANCH_PREFIX="${PR_BRANCH_PREFIX:-release-please--}"

# 放行一个"不合并"的结论，但流程继续（绿）
hold() {
  echo "$1"
  echo "approved=false" >> "${GITHUB_OUTPUT:?}"
  exit 0
}

# 明确的拒绝：让 CI 变红，逼人来看
deny() {
  echo "::error::$1" >&2
  echo "approved=false" >> "${GITHUB_OUTPUT:?}"
  exit 1
}

# ── 1. 找出待处理的发版申请单 ──────────────────────────────────────────────
PR_NUMBER="$(gh pr list --state open --limit 50 --json number,headRefName \
  --jq "[.[] | select(.headRefName | startswith(\"$BRANCH_PREFIX\"))] | .[0].number // empty")"

if [ -z "$PR_NUMBER" ]; then
  hold "没有待处理的发版申请单。"
fi
echo "待审申请单：#$PR_NUMBER"

TITLE="$(gh pr view "$PR_NUMBER" --json title --jq .title)"
BRANCH="$(gh pr view "$PR_NUMBER" --json headRefName --jq .headRefName)"
echo "标题    ：$TITLE"
echo "来源分支：$BRANCH"

# ── 2. 改动文件白名单 ──────────────────────────────────────────────────────
FILES="$(gh pr view "$PR_NUMBER" --json files --jq '.files[].path')"
echo "改动文件："
printf '%s\n' "$FILES" | sed 's/^/  - /'

BAD="$(printf '%s\n' "$FILES" | grep -Ev "$ALLOWED_RE" || true)"
if [ -n "$BAD" ]; then
  deny "发版申请单夹带了白名单之外的文件改动，拒绝自动合并：
$(printf '%s\n' "$BAD" | sed 's/^/  - /')
（如果确有正当改动，请人工检查后手动合并。）"
fi
echo "文件白名单：通过 ✅"

# ── 3. 版本号校验 ──────────────────────────────────────────────────────────
VERSION="$(printf '%s' "$TITLE" | sed -n 's/.*release \([0-9][0-9.]*\).*/\1/p')"
if ! printf '%s' "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  deny "无法从申请单标题里解析出合法版本号。标题：$TITLE"
fi

CURRENT="$(python3 -c "import json;print(json.load(open('.release-please-manifest.json'))['.'])")"
if ! python3 - "$CURRENT" "$VERSION" <<'PY'
import sys
def key(s):
    return tuple(int(x) for x in s.split('.'))
cur, new = key(sys.argv[1]), key(sys.argv[2])
sys.exit(0 if new > cur else 1)
PY
then
  deny "版本号没有递增：$CURRENT → $VERSION"
fi
echo "版本号：$CURRENT → $VERSION ✅"

# ── 4. 变更说明留痕 ────────────────────────────────────────────────────────
echo "变更说明摘要（前 30 行）："
gh pr view "$PR_NUMBER" --json body --jq .body | head -30 | sed 's/^/  /'

{
  echo "approved=true"
  echo "pr_number=$PR_NUMBER"
  echo "version=$VERSION"
} >> "$GITHUB_OUTPUT"

echo "审查通过，放行自动合并 ✅"
