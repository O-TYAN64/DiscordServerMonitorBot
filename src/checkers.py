"""
checkers.py  –  サーバー種別ごとのステータス確認モジュール

対応種別:
  ゲームサーバー : minecraft / ark / valheim / rust / cs2 / palworld
                   7dtd / terraria / vrchat / steam_query (汎用 A2S)
  インフラ API   : aws / cloudflare
  Web/HTTP       : web
  汎用 API       : api (カスタム REST エンドポイント)
  Steam Web API  : steam_server_list
  Game Server API: game_server_api (api.gameserverapi.com)
"""

from __future__ import annotations

import asyncio
import os
import socket
import struct
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp

# ─── 共通ユーティリティ ─────────────────────────────────────────

def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def tcp_ping(host: str, port: int, timeout: float = 5.0) -> tuple[bool, float]:
    """TCP 接続で死活確認。(online, latency_ms)"""
    try:
        t0 = time.perf_counter()
        with socket.create_connection((host, port), timeout=timeout):
            return True, round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        return False, -1


def udp_ping(host: str, port: int, payload: bytes, timeout: float = 5.0) -> tuple[bool, float, bytes]:
    """UDP 送信して応答を待つ。(online, latency_ms, response_bytes)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        t0 = time.perf_counter()
        sock.sendto(payload, (host, port))
        data, _ = sock.recvfrom(4096)
        latency = round((time.perf_counter() - t0) * 1000, 1)
        sock.close()
        return True, latency, data
    except Exception:
        return False, -1, b""


# ─── A2S_INFO (Steam Query Protocol) ──────────────────────────

A2S_REQUEST = b"\xFF\xFF\xFF\xFFTSource Engine Query\x00"


def _parse_a2s(data: bytes) -> dict:
    """Steam A2S_INFO レスポンスをパース"""
    if len(data) < 6 or data[4:5] not in (b"I", b"m"):
        return {}
    idx = 5

    def rs():
        nonlocal idx
        end = data.index(b"\x00", idx)
        s = data[idx:end].decode("utf-8", errors="replace")
        idx = end + 1
        return s

    def rb():
        nonlocal idx
        v = data[idx]; idx += 1; return v

    def rsh():
        nonlocal idx
        v = struct.unpack_from("<H", data, idx)[0]; idx += 2; return v

    try:
        idx += 1  # protocol
        name = rs(); map_ = rs(); rs(); rs()
        app_id = rsh()
        players = rb(); max_players = rb(); bots = rb()
        return {
            "server_name": name, "map": map_, "app_id": app_id,
            "players": players, "max_players": max_players, "bots": bots,
        }
    except Exception:
        return {}


def a2s_info(host: str, port: int) -> dict:
    online, latency, data = udp_ping(host, port, A2S_REQUEST)
    result = {"online": online, "latency_ms": latency}
    if online:
        result.update(_parse_a2s(data))
    return result


# ─── Minecraft (TCP + MOTD SLP) ───────────────────────────────

def _mc_slp(host: str, port: int) -> dict:
    """Minecraft Server List Ping (1.7+)"""
    import json as _json
    try:
        sock = socket.socket()
        sock.settimeout(5)
        t0 = time.perf_counter()
        sock.connect((host, port))

        def pack_varint(v: int) -> bytes:
            buf = b""
            while True:
                b = v & 0x7F
                v >>= 7
                buf += bytes([b | (0x80 if v else 0)])
                if not v:
                    break
            return buf

        def read_varint(s) -> int:
            n = shift = 0
            while True:
                b = s.recv(1)[0]
                n |= (b & 0x7F) << shift
                if not (b & 0x80):
                    return n
                shift += 7

        host_bytes = host.encode()
        handshake = (
            pack_varint(0x00)
            + pack_varint(47)
            + pack_varint(len(host_bytes)) + host_bytes
            + struct.pack(">H", port)
            + pack_varint(1)
        )
        sock.send(pack_varint(len(handshake)) + handshake)
        sock.send(b"\x01\x00")

        read_varint(sock)  # length
        read_varint(sock)  # packet id
        json_len = read_varint(sock)
        raw = b""
        while len(raw) < json_len:
            chunk = sock.recv(json_len - len(raw))
            if not chunk:
                break
            raw += chunk
        sock.close()

        latency = round((time.perf_counter() - t0) * 1000, 1)
        data = _json.loads(raw.decode("utf-8"))
        desc = data.get("description", {})
        motd = desc.get("text", "") if isinstance(desc, dict) else str(desc)
        players = data.get("players", {})
        version = data.get("version", {})
        return {
            "online": True,
            "latency_ms": latency,
            "motd": motd,
            "players": players.get("online", 0),
            "max_players": players.get("max", 0),
            "version": version.get("name", ""),
        }
    except Exception as e:
        return {"online": False, "error": str(e)}


async def check_minecraft(info: dict, _session) -> dict:
    result = await asyncio.get_event_loop().run_in_executor(
        None, _mc_slp, info["host"], info["port"]
    )
    result["type"] = "minecraft"
    return result


# ─── Valheim (Steam A2S, UDP 2457) ────────────────────────────

async def check_valheim(info: dict, _session) -> dict:
    r = await asyncio.get_event_loop().run_in_executor(
        None, a2s_info, info["host"], info["port"]
    )
    r["type"] = "valheim"
    return r


# ─── ARK: Survival Evolved (Steam A2S, UDP 7777) ──────────────

async def check_ark(info: dict, _session) -> dict:
    r = await asyncio.get_event_loop().run_in_executor(
        None, a2s_info, info["host"], info["port"]
    )
    r["type"] = "ark"
    return r


# ─── Rust (Steam A2S, UDP 28015) ──────────────────────────────

async def check_rust(info: dict, _session) -> dict:
    r = await asyncio.get_event_loop().run_in_executor(
        None, a2s_info, info["host"], info["port"]
    )
    r["type"] = "rust"
    return r


# ─── CS2 / CS:GO (Steam A2S, UDP 27015) ───────────────────────

async def check_cs2(info: dict, _session) -> dict:
    r = await asyncio.get_event_loop().run_in_executor(
        None, a2s_info, info["host"], info["port"]
    )
    r["type"] = "cs2"
    return r


# ─── Palworld (Steam A2S, UDP 8211) ───────────────────────────

async def check_palworld(info: dict, _session) -> dict:
    r = await asyncio.get_event_loop().run_in_executor(
        None, a2s_info, info["host"], info["port"]
    )
    r["type"] = "palworld"
    return r


# ─── 7 Days to Die (Steam A2S, UDP 26900) ─────────────────────

async def check_7dtd(info: dict, _session) -> dict:
    r = await asyncio.get_event_loop().run_in_executor(
        None, a2s_info, info["host"], info["port"]
    )
    r["type"] = "7dtd"
    return r


# ─── Terraria (TCP ping のみ、REST MOD 対応) ──────────────────

async def check_terraria(info: dict, session: aiohttp.ClientSession) -> dict:
    host, port = info["host"], info["port"]
    online, latency = await asyncio.get_event_loop().run_in_executor(
        None, tcp_ping, host, port
    )
    result: dict[str, Any] = {"type": "terraria", "online": online, "latency_ms": latency}

    # tModLoader REST API が有効な場合
    rest_port = info.get("rest_port")
    if online and rest_port:
        try:
            url = f"http://{host}:{rest_port}/v2/server/status"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    result["server_name"] = data.get("name", "")
                    result["players"] = len(data.get("players", {}).get("players", []))
                    result["max_players"] = data.get("maxplayers", 0)
                    result["world"] = data.get("world", "")
        except Exception:
            pass
    return result


# ─── VRChat (公式 API) ─────────────────────────────────────────

async def check_vrchat(info: dict, session: aiohttp.ClientSession) -> dict:
    world_id = info["host"]
    result: dict[str, Any] = {"type": "vrchat", "world_id": world_id}
    try:
        url = f"https://api.vrchat.cloud/api/1/worlds/{world_id}"
        headers = {"User-Agent": "DiscordServerMonitor/2.0"}
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                d = await resp.json()
                result.update({
                    "online": True,
                    "world_name": d.get("name", ""),
                    "author": d.get("authorName", ""),
                    "occupants": d.get("occupants", 0),
                    "public_occupants": d.get("publicOccupants", 0),
                    "private_occupants": d.get("privateOccupants", 0),
                    "capacity": d.get("capacity", 0),
                    "updated_at": d.get("updatedAt", ""),
                })
            else:
                result.update({"online": False, "error": f"HTTP {resp.status}"})
    except Exception as e:
        result.update({"online": False, "error": str(e)})
    return result


# ─── 汎用 Steam Query (A2S) ────────────────────────────────────

async def check_steam_query(info: dict, _session) -> dict:
    r = await asyncio.get_event_loop().run_in_executor(
        None, a2s_info, info["host"], info["port"]
    )
    r["type"] = "steam_query"
    return r


# ─── Web / HTTP ────────────────────────────────────────────────

async def check_web(info: dict, session: aiohttp.ClientSession) -> dict:
    host, port = info["host"], info["port"]
    scheme = info.get("scheme", "https" if port == 443 else "http")
    url = f"{scheme}://{host}" + (f":{port}" if port not in (80, 443) else "")
    result: dict[str, Any] = {"type": "web", "url": url}
    try:
        t0 = time.perf_counter()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8), ssl=False) as resp:
            result.update({
                "online": True,
                "status_code": resp.status,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                "content_type": resp.headers.get("Content-Type", ""),
            })
    except Exception as e:
        result.update({"online": False, "error": str(e)})
    return result


# ─── 汎用カスタム REST API ─────────────────────────────────────

async def check_api(info: dict, session: aiohttp.ClientSession) -> dict:
    """
    info フィールド:
      host        : ベース URL (例: https://myserver.com)
      endpoint    : パス (例: /api/v1/status)
      method      : GET/POST (省略時 GET)
      headers_json: 追加ヘッダー JSON 文字列
      expect_key  : レスポンス JSON からオンライン判定に使うキー (省略時 status_code で判断)
      expect_value: expect_key の期待値 (省略時に非 null で online=True)
    """
    import json as _json
    host = info["host"].rstrip("/")
    endpoint = info.get("endpoint", "/")
    url = host + endpoint
    method = info.get("method", "GET").upper()
    headers = {}
    if info.get("headers_json"):
        try:
            headers = _json.loads(info["headers_json"])
        except Exception:
            pass

    result: dict[str, Any] = {"type": "api", "url": url}
    try:
        t0 = time.perf_counter()
        async with session.request(
            method, url, headers=headers, timeout=aiohttp.ClientTimeout(total=8), ssl=False
        ) as resp:
            latency = round((time.perf_counter() - t0) * 1000, 1)
            body = await resp.text()
            try:
                body_json = _json.loads(body)
            except Exception:
                body_json = None

            expect_key = info.get("expect_key")
            if expect_key and body_json and isinstance(body_json, dict):
                val = body_json.get(expect_key)
                expect_val = info.get("expect_value")
                online = (str(val) == str(expect_val)) if expect_val is not None else (val is not None)
            else:
                online = resp.status < 400

            result.update({
                "online": online,
                "status_code": resp.status,
                "latency_ms": latency,
                "response_snippet": body[:200] if body else "",
            })
    except Exception as e:
        result.update({"online": False, "error": str(e)})
    return result


# ─── Steam Web API (ISteamApps/GetServers or IGameServersService) ──

async def check_steam_server_list(info: dict, session: aiohttp.ClientSession) -> dict:
    """
    Steam Web API でサーバーを検索して情報を取得する。
    info フィールド:
      host     : サーバーの IP:port (例: 192.168.1.1:27015)
      steam_key: Steam Web API キー (env STEAM_API_KEY でも可)
    """
    api_key = info.get("steam_key") or os.environ.get("STEAM_API_KEY", "")
    addr = f"{info['host']}:{info['port']}"
    result: dict[str, Any] = {"type": "steam_server_list", "addr": addr}

    if not api_key:
        result.update({"online": False, "error": "STEAM_API_KEY が未設定です"})
        return result

    url = "https://api.steampowered.com/IGameServersService/GetServerList/v1/"
    params = {"key": api_key, "filter": f"addr\\{addr}", "limit": 1}
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status != 200:
                result.update({"online": False, "error": f"Steam API HTTP {resp.status}"})
                return result
            data = await resp.json()
            servers = data.get("response", {}).get("servers", [])
            if not servers:
                result.update({"online": False, "error": "Steam API にサーバーが見つかりません (非公開の可能性)"})
                return result
            s = servers[0]
            result.update({
                "online": True,
                "server_name": s.get("name", ""),
                "map": s.get("map", ""),
                "players": s.get("players", 0),
                "max_players": s.get("max_players", 0),
                "bots": s.get("bots", 0),
                "game": s.get("gamedir", ""),
                "version": s.get("version", ""),
                "os": s.get("os", ""),
                "vac": s.get("secure", False),
            })
    except Exception as e:
        result.update({"online": False, "error": str(e)})
    return result


# ─── Game Server API (api.gameserverapi.com) ──────────────────

async def check_game_server_api(info: dict, session: aiohttp.ClientSession) -> dict:
    """
    https://www.gameserverapi.com/ の汎用ゲームサーバー API
    info フィールド:
      host        : サーバーの IP
      port        : サーバーのポート
      game        : ゲーム識別子 (例: minecraft, rust, csgo, ark, valheim …)
      gsa_api_key : API キー (env GAME_SERVER_API_KEY でも可)
    """
    api_key = info.get("gsa_api_key") or os.environ.get("GAME_SERVER_API_KEY", "")
    game = info.get("game", "")
    result: dict[str, Any] = {"type": "game_server_api", "host": info["host"], "port": info["port"], "game": game}

    url = f"https://api.gameserverapi.com/v1/servers/{info['host']}:{info['port']}"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    params = {}
    if game:
        params["game"] = game

    try:
        async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                d = await resp.json()
                result.update({
                    "online": d.get("online", False),
                    "server_name": d.get("name", ""),
                    "map": d.get("map", ""),
                    "players": d.get("players", {}).get("online", 0),
                    "max_players": d.get("players", {}).get("max", 0),
                    "version": d.get("version", ""),
                    "latency_ms": d.get("ping", -1),
                    "raw": d,
                })
            else:
                result.update({"online": False, "error": f"HTTP {resp.status}"})
    except Exception as e:
        result.update({"online": False, "error": str(e)})
    return result


# ─── AWS インフラ ──────────────────────────────────────────────

async def check_aws(info: dict, session: aiohttp.ClientSession) -> dict:
    """
    AWS Health Dashboard / Service Status を確認。
    info フィールド:
      host    : region または "global" (例: ap-northeast-1)
      services: カンマ区切りのサービス名 (省略時は EC2/RDS/S3)
    """
    region = info.get("host", "global")
    result: dict[str, Any] = {"type": "aws", "region": region}
    services_filter = [s.strip().lower() for s in info.get("services", "ec2,rds,s3").split(",")]

    # AWS Status JSON (公式フィード)
    feed_url = "https://health.aws.amazon.com/public/currentevents"
    try:
        async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                events = data if isinstance(data, list) else data.get("events", [])
                # 対象リージョンのイベントを絞り込む
                affected = []
                for ev in events:
                    affected_regions = [r.get("regionName", "") for r in ev.get("affectedEntities", [])]
                    svc = ev.get("service", "").lower()
                    if (region == "global" or region in affected_regions or not affected_regions):
                        if any(s in svc for s in services_filter) or not services_filter:
                            affected.append({
                                "service": ev.get("service", ""),
                                "summary": ev.get("eventDescription", [{}])[0].get("latestDescription", "")[:100],
                                "status": ev.get("statusCode", ""),
                            })
                result["online"] = True
                result["healthy"] = len(affected) == 0
                result["active_events"] = affected[:5]
                result["event_count"] = len(affected)
            else:
                # フォールバック: 簡易 ping
                online, latency = await asyncio.get_event_loop().run_in_executor(
                    None, tcp_ping, f"ec2.{region}.amazonaws.com", 443
                )
                result.update({"online": online, "latency_ms": latency, "note": "Health API 取得失敗、TCP ping で代替"})
    except Exception as e:
        # フォールバック
        online, latency = await asyncio.get_event_loop().run_in_executor(
            None, tcp_ping, f"ec2.{region}.amazonaws.com", 443
        )
        result.update({"online": online, "latency_ms": latency, "error": str(e)})
    return result


# ─── Cloudflare インフラ ───────────────────────────────────────

async def check_cloudflare(info: dict, session: aiohttp.ClientSession) -> dict:
    """
    Cloudflare Status API を確認。
    info フィールド:
      host      : "global" または datacenters のコード (例: NRT)
      cf_api_key: Cloudflare API キー (オプション、追加情報取得用)
      cf_zone_id: Zone ID (オプション、ゾーン固有の確認用)
    """
    result: dict[str, Any] = {"type": "cloudflare"}

    # Cloudflare Status Page API
    try:
        url = "https://www.cloudflarestatus.com/api/v2/summary.json"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                data = await resp.json()
                status = data.get("status", {})
                components = data.get("components", [])
                incidents = data.get("incidents", [])

                overall = status.get("indicator", "unknown")
                result.update({
                    "online": True,
                    "healthy": overall == "none",
                    "overall_status": status.get("description", ""),
                    "indicator": overall,
                    "active_incidents": [
                        {"name": i.get("name", ""), "impact": i.get("impact", ""), "status": i.get("status", "")}
                        for i in incidents[:3]
                    ],
                    "degraded_components": [
                        c.get("name", "") for c in components
                        if c.get("status", "operational") != "operational"
                    ][:5],
                })

                # ゾーン固有の確認 (Cloudflare API キーが必要)
                cf_key = info.get("cf_api_key") or os.environ.get("CF_API_KEY", "")
                cf_zone = info.get("cf_zone_id") or os.environ.get("CF_ZONE_ID", "")
                if cf_key and cf_zone:
                    zone_url = f"https://api.cloudflare.com/client/v4/zones/{cf_zone}"
                    headers = {"Authorization": f"Bearer {cf_key}"}
                    async with session.get(zone_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as zresp:
                        if zresp.status == 200:
                            zdata = await zresp.json()
                            zone_info = zdata.get("result", {})
                            result["zone_name"] = zone_info.get("name", "")
                            result["zone_status"] = zone_info.get("status", "")
                            result["zone_plan"] = zone_info.get("plan", {}).get("name", "")
            else:
                result.update({"online": False, "error": f"Status API HTTP {resp.status}"})
    except Exception as e:
        result.update({"online": False, "error": str(e)})
    return result


# ─── チェッカー登録テーブル ────────────────────────────────────

CHECKERS: dict[str, Any] = {
    "minecraft":        check_minecraft,
    "ark":              check_ark,
    "valheim":          check_valheim,
    "rust":             check_rust,
    "cs2":              check_cs2,
    "csgo":             check_cs2,
    "palworld":         check_palworld,
    "7dtd":             check_7dtd,
    "terraria":         check_terraria,
    "vrchat":           check_vrchat,
    "steam_query":      check_steam_query,
    "web":              check_web,
    "api":              check_api,
    "steam_server_list": check_steam_server_list,
    "game_server_api":  check_game_server_api,
    "aws":              check_aws,
    "cloudflare":       check_cloudflare,
}

SUPPORTED_TYPES = sorted(CHECKERS.keys())


async def run_check(key: str, info: dict, session: aiohttp.ClientSession) -> dict:
    """種別に応じたチェック関数を呼び出す"""
    t = info.get("type", "web")
    fn = CHECKERS.get(t)
    if fn is None:
        return {"type": t, "online": False, "error": f"未対応の種別: {t}"}
    try:
        return await fn(info, session)
    except Exception as e:
        return {"type": t, "online": False, "error": str(e)}
