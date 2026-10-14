#!/usr/bin/env python3
"""
压缩技能包内的位图资源（PNG -> JPEG），用于控制发布体积。

为什么需要：
  - LobeHub Market 的技能发布走 ZIP 上传，包体过大会被拒（实测 16MB -> Payload Too Large）。
  - 用户 `npx skills add owner/repo` 会整包下载，体积直接决定安装体验。
  - 原始 PNG 为 1024x1536 的 AI 输出，单张 ~2.5MB，7 张共 ~16MB，属于「无谓的体积」。

策略：
  - 风格参考图 assets/styles/<id>/ref.png —— 功能性资产（按 image1 传入做风格锚定），
    保留 1024x1536 分辨率，JPEG q92，避免损失风格质感。
  - 案例成图 assets/cases/images/*.png —— 仅作示例归档，降到 768 宽、JPEG q88。

用法：
  python3 scripts/optimize-assets.py            # 执行
  python3 scripts/optimize-assets.py --dry-run  # 只看结果不落盘
"""

import argparse
import os
import sys

from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(REPO, "skills", "muse-illustration")

REF_QUALITY = 92
CASES_QUALITY = 88
CASES_WIDTH = 768


def human(n: int) -> str:
    return f"{n / 1024:.0f} KB" if n < 1024 * 1024 else f"{n / 1024 / 1024:.2f} MB"


def convert(src: str, dst: str, quality: int, max_width: int | None, dry: bool) -> tuple[int, int]:
    im = Image.open(src).convert("RGB")
    if max_width and im.width > max_width:
        h = round(im.height * max_width / im.width)
        im = im.resize((max_width, h), Image.LANCZOS)
    before = os.path.getsize(src)
    if not dry:
        im.save(dst, quality=quality, optimize=True, progressive=True)
    after = os.path.getsize(dst) if not dry else 0
    return before, after


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total_before = total_after = 0

    # 1) 风格参考图：保持分辨率，只换编码
    styles_dir = os.path.join(SKILL, "assets", "styles")
    for sid in sorted(os.listdir(styles_dir)):
        png = os.path.join(styles_dir, sid, "ref.png")
        if not os.path.exists(png):
            continue
        jpg = os.path.join(styles_dir, sid, "ref.jpg")
        b, a = convert(png, jpg, REF_QUALITY, None, args.dry_run)
        total_before += b
        total_after += a or b * 0.22
        print(f"[ref]   {sid:16s} {human(b):>9s} -> {human(int(a or b * 0.22)):>9s}  ref.png => ref.jpg")
        if not args.dry_run:
            os.remove(png)

    # 2) 案例成图：降分辨率，仅作示例
    cases_img = os.path.join(SKILL, "assets", "cases", "images")
    for name in sorted(os.listdir(cases_img)):
        if not name.endswith(".png"):
            continue
        src = os.path.join(cases_img, name)
        dst = os.path.join(cases_img, name[:-4] + ".jpg")
        b, a = convert(src, dst, CASES_QUALITY, CASES_WIDTH, args.dry_run)
        total_before += b
        total_after += a or b * 0.10
        print(f"[case]  {name:42s} {human(b):>9s} -> {human(int(a or b * 0.10)):>9s}")
        if not args.dry_run:
            os.remove(src)

    print("-" * 62)
    print(f"合计: {human(int(total_before))} -> {human(int(total_after))}  "
          f"(省 {100 * (1 - total_after / total_before):.0f}%)")
    if args.dry_run:
        print("(dry-run，未落盘)")
    else:
        print("已完成。记得同步更新 meta.yaml 的 ref: 与案例 md 的图片路径。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
