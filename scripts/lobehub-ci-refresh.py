#!/usr/bin/env python3
"""在 CI 里刷新 LobeHub 用户令牌，并把轮换后的 refresh_token 写回 GitHub Secret。

为什么要这么绕（三条实测结论）：

1. LobeHub 的发布接口要的是**用户级**令牌。
   用 M2M 的 clientId/clientSecret 换来的令牌只代表 CLI 客户端自己
   （JWT claims 只有 sub=cli_xxx，没有用户身份），拿去调 /v1/user/skills
   会直接回 invalid_token。所以 M2M 这条路走不通。

2. 用户令牌只能靠 refresh_token 离线续期，
   端点是 POST {base}/lobehub-oidc/token，
   参数 grant_type=refresh_token & refresh_token=<RT> & client_id=lobehub-cli。
   换回来的 access_token 有效期 604800 秒（7 天）。

3. **服务端每次刷新都会轮换 refresh_token**，旧值立刻作废
   （实测：拿旧 RT 再刷 → HTTP 400 invalid_grant）。
   所以刷新之后必须马上把新值持久化，否则下一次 CI 就没得用了。

环境变量：
  LOBEHUB_REFRESH_TOKEN  必填。LobeHub 用户 refresh_token（首值来自本地 lhm login）
  GH_SECRETS_PAT         选填。细粒度 PAT，权限 Secrets = Read and write。
                         不填则只写本地凭据文件、跳过写回（会告警）。
  LOBEHUB_BASE_URL       选填，默认 https://market.lobehub.com
  LOBEHUB_SECRET_NAME    选填，默认 LOBEHUB_REFRESH_TOKEN

退出码：0 成功；1 失败（refresh_token 失效 / 写回失败）
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = os.environ.get("LOBEHUB_BASE_URL", "https://market.lobehub.com").rstrip("/")
CLIENT_ID = "lobehub-cli"
CRED = Path.home() / ".lobehub-market" / "user-credentials.json"
SECRET_NAME = os.environ.get("LOBEHUB_SECRET_NAME", "LOBEHUB_REFRESH_TOKEN")
TOKEN_URL = f"{BASE}/lobehub-oidc/token"


def die(msg: str) -> None:
    print(f"::error::{msg}", file=sys.stderr)
    sys.exit(1)


def mask(value: str) -> None:
    """让 GitHub 日志自动打码。必须在任何可能打印之前调用。"""
    if os.environ.get("GITHUB_ACTIONS") == "true" and value:
        print(f"::add-mask::{value}", flush=True)


def jwt_claim(token: str, key: str) -> str:
    """不验签地读一个 JWT claim。这里只用于把 id_token 里的 userId 取出来填档案。"""
    try:
        body = token.split(".")[1]
        body += "=" * (-len(body) % 4)
        return str(json.loads(base64.urlsafe_b64decode(body)).get(key) or "")
    except Exception:  # noqa: BLE001
        return ""


def main() -> int:
    rt = os.environ.get("LOBEHUB_REFRESH_TOKEN", "").strip()
    if not rt:
        die("缺少环境变量 LOBEHUB_REFRESH_TOKEN")
    mask(rt)

    print("── 刷新 LobeHub 用户令牌 ────────────────────────────────")

    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": rt,
            "client_id": CLIENT_ID,
        }
    ).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            tok = json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        die(
            f"刷新被拒：HTTP {exc.code} {detail}。"
            "多半是 refresh_token 已经失效（被某次刷新轮换过、但新值没写回）。"
            "处理：在本地跑 `npx -y @lobehub/market-cli login`，"
            f"把 ~/.lobehub-market/user-credentials.json 里的 refreshToken 更新到 Secret {SECRET_NAME}。"
        )
    except Exception as exc:  # noqa: BLE001
        die(f"刷新请求失败：{exc}")

    at = tok.get("access_token")
    new_rt = tok.get("refresh_token")
    if not at or not new_rt:
        die(f"刷新响应缺少令牌字段：{sorted(tok)}")
    mask(at)
    mask(new_rt)

    expires = datetime.now(timezone.utc) + timedelta(seconds=int(tok.get("expires_in", 604800)))
    user_id_from_token = jwt_claim(tok.get("id_token", ""), "sub")

    # 保留 CI 里可能存在的身份字段；本地文件缺失时用环境变量兜底。
    old: dict = {}
    if CRED.exists():
        try:
            old = json.loads(CRED.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            old = {}

    CRED.parent.mkdir(parents=True, exist_ok=True)
    CRED.write_text(
        json.dumps(
            {
                "accessToken": at,
                "baseUrl": old.get("baseUrl") or BASE,
                "displayName": old.get("displayName") or os.environ.get("LOBEHUB_DISPLAY_NAME", ""),
                "email": old.get("email") or os.environ.get("LOBEHUB_EMAIL", ""),
                "expiresAt": expires.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "refreshToken": new_rt,
                "userId": old.get("userId") or user_id_from_token or os.environ.get("LOBEHUB_USER_ID", ""),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    CRED.chmod(0o600)
    print(f"  已写入 {CRED}")
    print(f"  access_token 有效期至 {expires:%Y-%m-%d %H:%M UTC}")

    gh_pat = os.environ.get("GH_SECRETS_PAT", "").strip()
    if not gh_pat:
        print(
            "::warning::未提供 GH_SECRETS_PAT，跳过写回。"
            f"Secret {SECRET_NAME} 里现在存的是已经作废的旧 refresh_token，"
            "下一次发布必然失败——请在本地重新 login 并更新该 Secret。"
        )
        return 0

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    ok = False
    for attempt in range(1, 4):
        proc = subprocess.run(
            ["gh", "secret", "set", SECRET_NAME, "--repo", repo],
            input=new_rt,
            env={**os.environ, "GH_TOKEN": gh_pat},
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            ok = True
            print(f"  已把轮换后的 refresh_token 写回 Secret {SECRET_NAME}（第 {attempt} 次尝试）")
            break
        print(f"  写回失败（第 {attempt}/3 次）：{proc.stderr.strip()[:200]}", file=sys.stderr)
        time.sleep(3)

    if not ok:
        die(
            "写回 Secret 失败。refresh_token 已被轮换、旧值作废——"
            "请在本地重新 `npx -y @lobehub/market-cli login`，"
            f"再把新的 refreshToken 更新到 Secret {SECRET_NAME}。"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
