"""
check_status.py  –  GitHub Actions から呼ばれるステータスチェッカー
環境変数:
  SERVER_NAMES   : カンマ区切りのサーバー識別名 (例: "mc1,web1,ark1")
  DISCORD_WEBHOOK: 結果を投稿する Discord Webhook URL
"""

import os
import json
import asyncio
import socket
import time
from datetime import datetime, timezone

import aiohttp

# ─── 設定読み込み ───────────────────────────────────────────────
SERVERS_JSON = os.path.join(os.path.dirname(__file__), "..", "config", "servers.json")
SERVER_NAMES = [s.strip() for s in os.environ.get("SERVER_NAMES", "all").split(",") if s.strip()]
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]


def load_servers() -> dict:
    with open(SERVERS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── 各種チェック関数 ───────────────────────────────────────────

def ping_tcp(host: str, port: int, timeout: float = 5.0) -> tuple[bool, float]:
    """TCP 接続で死活確認。(online, latency_ms) を返す"""
    try:
        start = time.perf_counter()
        with socket.create_connection((host, port), timeout=timeout):
            latency = (time.perf_counter() - start) * 1000
        return True, round(latency, 1)
    except Exception:
        return False, -1


async def check_web(host: str, port: int, session: aiohttp.ClientSession) -> dict:
    """HTTP(S) エンドポイントの確認"""
    scheme = "https" if port == 443 else "http"
    url = f"{scheme}://{host}" + (f":{port}" if port not in (80, 443) else "")
    result = {"type": "web", "url": url}
    try:
        start = time.perf_counter()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8), ssl=False) as resp:
            latency = (time.perf_counter() - start) * 1000
            result["online"] = True
            result["status_code"] = resp.status
            result["latency_ms"] = round(latency, 1)
    except Exception as e:
        result["online"] = False
        result["error"] = str(e)
    return result


async def check_ark(host: str, port: int) -> dict:
    """
    ARK: Survival Evolved  –  Steamworks A2S_INFO クエリ (UDP)
    完全実装には steam-query ライブラリが必要なため、
    ここでは TCP ping + UDP A2S_INFO 簡易実装を行う。
    """
    result = {"type": "ark", "host": host, "port": port}

    # まず TCP で生死確認 (RCON ポートは port+1 のことが多いが game port で試す)
    online, latency = ping_tcp(host, port)
    result["online"] = online
    result["latency_ms"] = latency

    if online:
        # A2S_INFO UDP クエリ
        A2S_REQUEST = b"\xFF\xFF\xFF\xFFTSource Engine Query\x00"
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _a2s_query, host, port, A2S_REQUEST)
            if info:
                result.update(info)
        except Exception:
            pass

    return result


def _a2s_query(host: str, port: int, payload: bytes) -> dict | None:
    """UDP A2S_INFO クエリの同期実装"""
    import struct

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        sock.sendto(payload, (host, port))
        data, _ = sock.recvfrom(4096)
        sock.close()

        if len(data) < 6 or data[4:5] != b"I":
            return None

        # パース (Steam A2S_INFO response)
        idx = 5  # skip header + type

        def read_str():
            nonlocal idx
            end = data.index(b"\x00", idx)
            s = data[idx:end].decode("utf-8", errors="replace")
            idx = end + 1
            return s

        def read_byte():
            nonlocal idx
            v = data[idx]
            idx += 1
            return v

        def read_short():
            nonlocal idx
            v = struct.unpack_from("<H", data, idx)[0]
            idx += 2
            return v

        idx += 1  # protocol
        server_name = read_str()
        map_name = read_str()
        read_str()  # folder
        read_str()  # game
        read_short()  # app id
        players = read_byte()
        max_players = read_byte()

        return {
            "server_name": server_name,
            "map": map_name,
            "players": players,
            "max_players": max_players,
        }
    except Exception:
        return None


async def check_vrchat(host: str, port: int, session: aiohttp.ClientSession) -> dict:
    """
    VRChat はクライアントアプリなので公式 API でワールド/インスタンス情報を取得する。
    host フィールドには VRChat World ID または Instance ID を記入することを想定。
    例: host = "wrld_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    """
    result = {"type": "vrchat", "world_id": host}
    api_url = f"https://api.vrchat.cloud/api/1/worlds/{host}"
    headers = {"User-Agent": "DiscordServerMonitor/1.0"}
    try:
        async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                data = await resp.json()
                result["online"] = True
                result["world_name"] = data.get("name", "Unknown")
                result["author"] = data.get("authorName", "Unknown")
                result["occupants"] = data.get("occupants", 0)
                result["public_occupants"] = data.get("publicOccupants", 0)
                result["private_occupants"] = data.get("privateOccupants", 0)
                result["capacity"] = data.get("capacity", 0)
                result["tags"] = data.get("tags", [])
            else:
                result["online"] = False
                result["error"] = f"HTTP {resp.status}"
    except Exception as e:
        result["online"] = False
        result["error"] = str(e)
    return result


# ─── Embed 構築 ─────────────────────────────────────────────────

def build_embed(server_key: str, info: dict, result: dict) -> dict:
    """Discord Embed の dict を返す"""
    label = info.get("label", server_key)
    online = result.get("online", False)
    color = 0x2ECC71 if online else 0xE74C3C  # green / red
    status_icon = "🟢" if online else "🔴"
    server_type = result.get("type", info.get("type", ""))

    fields = []

    if server_type == "web":
        fields.append({"name": "URL", "value": result.get("url", "-"), "inline": False})
        if online:
            fields.append({"name": "HTTP ステータス", "value": str(result.get("status_code", "-")), "inline": True})
            fields.append({"name": "レイテンシ", "value": f"{result.get('latency_ms', '-')} ms", "inline": True})
        else:
            fields.append({"name": "エラー", "value": result.get("error", "不明"), "inline": False})

    elif server_type == "ark":
        fields.append({"name": "アドレス", "value": f"`{info['host']}:{info['port']}`", "inline": False})
        if online:
            fields.append({"name": "レイテンシ", "value": f"{result.get('latency_ms', '-')} ms", "inline": True})
            if "server_name" in result:
                fields.append({"name": "サーバー名", "value": result["server_name"], "inline": True})
                fields.append({"name": "マップ", "value": result.get("map", "-"), "inline": True})
                fields.append({
                    "name": "プレイヤー",
                    "value": f"{result.get('players', 0)} / {result.get('max_players', 0)}",
                    "inline": True,
                })

    elif server_type == "vrchat":
        fields.append({"name": "World ID", "value": f"`{info['host']}`", "inline": False})
        if online:
            fields.append({"name": "ワールド名", "value": result.get("world_name", "-"), "inline": True})
            fields.append({"name": "作者", "value": result.get("author", "-"), "inline": True})
            fields.append({
                "name": "滞在人数",
                "value": f"{result.get('occupants', 0)} 人 (公開: {result.get('public_occupants', 0)}, 非公開: {result.get('private_occupants', 0)})",
                "inline": False,
            })
            fields.append({"name": "容量", "value": str(result.get("capacity", "-")), "inline": True})
        else:
            fields.append({"name": "エラー", "value": result.get("error", "不明"), "inline": False})

    return {
        "title": f"{status_icon} {label}",
        "color": color,
        "fields": fields,
        "footer": {"text": f"種類: {server_type.upper()}  •  確認時刻: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"},
    }


# ─── メイン ─────────────────────────────────────────────────────

async def main():
    all_servers = load_servers()

    if SERVER_NAMES == ["all"]:
        targets = list(all_servers.keys())
    else:
        targets = [n for n in SERVER_NAMES if n in all_servers]

    if not targets:
        print("チェック対象のサーバーがありません")
        return

    embeds = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for key in targets:
            info = all_servers[key]
            t = info["type"]
            if t == "web":
                tasks.append((key, info, check_web(info["host"], info["port"], session)))
            elif t == "ark":
                tasks.append((key, info, check_ark(info["host"], info["port"])))
            elif t == "vrchat":
                tasks.append((key, info, check_vrchat(info["host"], info["port"], session)))

        results = await asyncio.gather(*[t[2] for t in tasks], return_exceptions=True)

        for (key, info, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                result = {"online": False, "type": info["type"], "error": str(result)}
            embeds.append(build_embed(key, info, result))

    # Discord Webhook に投稿 (embed は最大 10 件/リクエスト)
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(embeds), 10):
            payload = {"embeds": embeds[i : i + 10]}
            async with session.post(DISCORD_WEBHOOK, json=payload) as resp:
                if resp.status not in (200, 204):
                    text = await resp.text()
                    print(f"Discord Webhook error {resp.status}: {text}")
                else:
                    print(f"Posted {len(embeds[i:i+10])} embed(s) successfully")


if __name__ == "__main__":
    asyncio.run(main())
