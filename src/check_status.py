"""
check_status.py  –  GitHub Actions から実行されるステータスチェッカー

環境変数:
  SERVER_NAMES        : カンマ区切りのサーバー識別名 (all で全サーバー)
  DISCORD_WEBHOOK     : 結果を投稿する Discord Webhook URL
  STEAM_API_KEY       : Steam Web API キー (steam_server_list 種別で使用)
  GAME_SERVER_API_KEY : Game Server API キー (game_server_api 種別で使用)
  CF_API_KEY          : Cloudflare API キー (cloudflare 種別でゾーン確認に使用)
  CF_ZONE_ID          : Cloudflare Zone ID
"""

import asyncio
import json
import os
from pathlib import Path

import aiohttp

from checkers import run_check, SUPPORTED_TYPES
from embeds import build_embed

SERVERS_JSON = Path(__file__).parent.parent / "config" / "servers.json"
SERVER_NAMES = [s.strip() for s in os.environ.get("SERVER_NAMES", "all").split(",") if s.strip()]
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]


def load_servers() -> dict:
    with open(SERVERS_JSON, encoding="utf-8") as f:
        return json.load(f)


async def post_embeds(session: aiohttp.ClientSession, embeds: list[dict]):
    """Discord Webhook に embed を投稿 (10件/リクエスト制限)"""
    for i in range(0, len(embeds), 10):
        payload = {"embeds": embeds[i:i + 10]}
        async with session.post(DISCORD_WEBHOOK, json=payload) as resp:
            if resp.status not in (200, 204):
                text = await resp.text()
                print(f"[WARN] Discord Webhook {resp.status}: {text}")
            else:
                print(f"[OK] Posted {len(embeds[i:i+10])} embed(s)")


async def main():
    all_servers = load_servers()

    targets = list(all_servers.keys()) if SERVER_NAMES == ["all"] else [
        n for n in SERVER_NAMES if n in all_servers
    ]

    if not targets:
        print("チェック対象のサーバーがありません")
        return

    print(f"チェック対象: {', '.join(targets)}")

    embeds: list[dict] = []
    async with aiohttp.ClientSession() as session:
        tasks = [(key, all_servers[key], run_check(key, all_servers[key], session)) for key in targets]
        results = await asyncio.gather(*[t[2] for t in tasks], return_exceptions=True)

        for (key, info, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                result = {"type": info.get("type", "?"), "online": False, "error": str(result)}
            print(f"  {key}: online={result.get('online')} type={result.get('type')}")
            embeds.append(build_embed(key, info, result))

    # ヘッダー embed
    header = {
        "title": "📊 サーバーステータス レポート",
        "description": f"**{len(targets)}** サーバーを確認しました",
        "color": 0x5865F2,
        "fields": [{"name": "対応種別", "value": ", ".join(f"`{t}`" for t in SUPPORTED_TYPES), "inline": False}],
    }

    async with aiohttp.ClientSession() as session:
        await post_embeds(session, [header] + embeds)


if __name__ == "__main__":
    asyncio.run(main())
