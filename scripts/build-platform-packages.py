#!/usr/bin/env python3
"""为各技能市场生成可直接上传的成品包（本地构建产物，不入库）。

各市场对 SKILL.md frontmatter 的要求不一致：
  - 通用 / Claude / ZCode：只要求 name + description
  - WorkBuddy 开放平台：额外要求顶级字段 description_zh / description_en /
    version / author（我们的元数据默认放在 metadata: 下，需提升到顶层）

本脚本从 skills/muse-illustration 出发生成：
  dist/muse-illustration-workbuddy.zip      补全 WorkBuddy 必需字段后的技能包
  dist/muse-illustration-qoder.zip          原样技能包（Qoder 只要求 name+description）
  dist/muse-illustration-skill.zip          原样技能包（通用 / 备用）

用法：python3 scripts/build-platform-packages.py
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "skills", "muse-illustration")
DIST = os.path.join(REPO, "dist")

SKILL_NAME = "muse-illustration"

# WorkBuddy 顶层补充字段（内容与 SKILL.md 现有中英描述保持一致）
WB_EXTRA_FIELDS = [
    ("display_name", "灵感插图"),
    ("display_name_en", "Muse Illustration"),
    (
        "description_zh",
        "把诗词、词句、意象或一句话灵感，转化为插画或海报；内置可成长风格库"
        "（风格配方 = 正向提示词 + 负向约束 + 参考图 + 参数），支持选择风格、出图张数与成品形态。",
    ),
    (
        "description_en",
        "Turn poems, imagery, or a one-line spark of inspiration into illustrations "
        "or posters, using a growing built-in style library.",
    ),
    ("author", "Stayfoool"),
]

SKIP_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def read_skill_version() -> str:
    """从 SKILL.md 的 metadata.version 读取版本号。"""
    path = os.path.join(SRC, "SKILL.md")
    with open(path, encoding="utf-8") as fh:
        head = fh.read(4096)
    match = re.search(r'^\s{2}version:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?', head, re.M)
    if not match:
        raise SystemExit("无法从 SKILL.md 解析版本号")
    return match.group(1)


def split_frontmatter(text: str) -> tuple[str, str]:
    """拆出 YAML frontmatter 与正文。"""
    if not text.startswith("---\n"):
        raise SystemExit("SKILL.md 缺少 frontmatter")
    end = text.index("\n---\n", 4)
    return text[4 : end + 1], text[end + 5 :]


def augment_frontmatter(path: str, version: str) -> None:
    """把 WorkBuddy 必需字段提到 frontmatter 顶层。"""
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    fm, body = split_frontmatter(raw)

    # 只把「顶层」键算作已存在：metadata.version 是嵌套的，不能顶替顶层 version
    existing = {
        line.split(":", 1)[0].strip()
        for line in fm.splitlines()
        if ":" in line and not line[:1].isspace()
    }
    added = []
    for key, value in WB_EXTRA_FIELDS + [("version", version)]:
        if key in existing:
            continue
        added.append(f"{key}: {value}")

    if not added:
        return
    fm = fm.rstrip("\n") + "\n" + "\n".join(added) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"---\n{fm}---\n{body}")


def stage(dest_dir: str, version: str | None) -> None:
    """把技能目录复制到暂存区，可选地补全 WorkBuddy 字段。"""
    if os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
    shutil.copytree(
        SRC, dest_dir, ignore=lambda _d, names: [n for n in names if n in SKIP_NAMES]
    )
    if version is not None:
        augment_frontmatter(os.path.join(dest_dir, "SKILL.md"), version)


def zip_tree(source_dir: str, zip_path: str, root_name: str) -> tuple[int, int, str]:
    """打包；返回 (文件数, 字节数, sha256)。"""
    files = []
    for current, dirs, names in os.walk(source_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_NAMES)
        for name in sorted(names):
            if name in SKIP_NAMES:
                continue
            full = os.path.join(current, name)
            files.append((full, os.path.relpath(full, source_dir)))

    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for full, rel in files:
            zf.write(full, f"{root_name}/{rel}")

    digest = hashlib.sha256()
    with open(zip_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return len(files), os.path.getsize(zip_path), digest.hexdigest()


def main() -> None:
    version = read_skill_version()
    os.makedirs(DIST, exist_ok=True)

    staging = os.path.join(DIST, ".staging")
    if os.path.isdir(staging):
        shutil.rmtree(staging)

    plan = [
        ("workbuddy", version, f"muse-illustration-workbuddy-{version}.zip"),
        ("qoder", None, f"muse-illustration-qoder-{version}.zip"),
        ("generic", None, f"muse-illustration-skill-{version}.zip"),
    ]

    print(f"技能版本：{version}\n")
    print(f"{'目标':<12}{'文件':>5}{'大小':>12}  sha256")
    print("-" * 78)
    for label, inject, zip_name in plan:
        stage_dir = os.path.join(staging, label, SKILL_NAME)
        stage(stage_dir, inject)
        count, size, sha = zip_tree(stage_dir, os.path.join(DIST, zip_name), SKILL_NAME)
        print(f"{label:<12}{count:>5}{size / 1048576:>10.2f} MB  {sha[:16]}…")

    shutil.rmtree(staging)
    print(f"\n输出目录：{DIST}")


if __name__ == "__main__":
    main()
