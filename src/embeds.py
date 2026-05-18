"""
embeds.py  –  サーバー種別ごとの Discord Embed 生成
"""

from __future__ import annotations
from datetime import datetime, timezone


ICONS = {
    "minecraft":        "⛏️",
    "ark":              "🦕",
    "valheim":          "⚔️",
    "rust":             "🔫",
    "cs2":              "🎯",
    "csgo":             "🎯",
    "palworld":         "🌿",
    "7dtd":             "🧟",
    "terraria":         "🌳",
    "vrchat":           "🥽",
    "steam_query":      "🎮",
    "web":              "🌐",
    "api":              "🔌",
    "steam_server_list":"🎮",
    "game_server_api":  "🕹️",
    "aws":              "☁️",
    "cloudflare":       "🔶",
}

COLOR_OK   = 0x2ECC71  # green
COLOR_WARN = 0xF39C12  # orange
COLOR_ERR  = 0xE74C3C  # red


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _field(name: str, value: str, inline: bool = True) -> dict:
    return {"name": name, "value": str(value) or "—", "inline": inline}


def build_embed(server_key: str, info: dict, result: dict) -> dict:
    label = info.get("label", server_key)
    stype = result.get("type", info.get("type", ""))
    icon  = ICONS.get(stype, "🖥️")
    online = result.get("online", False)

    # カスタムステータスアイコン
    if stype in ("aws", "cloudflare"):
        healthy = result.get("healthy", online)
        status_icon = "🟢" if healthy else ("🟡" if online else "🔴")
        color = COLOR_OK if healthy else (COLOR_WARN if online else COLOR_ERR)
    else:
        status_icon = "🟢" if online else "🔴"
        color = COLOR_OK if online else COLOR_ERR

    fields: list[dict] = []

    # ─── ゲームサーバー共通 (A2S) ─────────────────────────────
    if stype in ("ark", "valheim", "rust", "cs2", "csgo", "palworld", "7dtd", "steam_query"):
        fields.append(_field("アドレス", f"`{info['host']}:{info['port']}`", False))
        if online:
            fields.append(_field("レイテンシ", f"{result.get('latency_ms', '—')} ms"))
            if "server_name" in result:
                fields.append(_field("サーバー名", result["server_name"], False))
                fields.append(_field("マップ",     result.get("map", "—")))
                p, mp = result.get("players", 0), result.get("max_players", 0)
                bar = _player_bar(p, mp)
                fields.append(_field("プレイヤー", f"{p} / {mp}  {bar}"))
                if result.get("bots", 0):
                    fields.append(_field("Bot 数", str(result["bots"])))
        else:
            fields.append(_field("エラー", result.get("error", "接続不可"), False))

    # ─── Minecraft ───────────────────────────────────────────
    elif stype == "minecraft":
        fields.append(_field("アドレス", f"`{info['host']}:{info['port']}`", False))
        if online:
            fields.append(_field("バージョン", result.get("version", "—")))
            fields.append(_field("レイテンシ", f"{result.get('latency_ms', '—')} ms"))
            p, mp = result.get("players", 0), result.get("max_players", 0)
            fields.append(_field("プレイヤー", f"{p} / {mp}  {_player_bar(p, mp)}"))
            if result.get("motd"):
                fields.append(_field("MOTD", result["motd"][:100], False))
        else:
            fields.append(_field("エラー", result.get("error", "接続不可"), False))

    # ─── Terraria ────────────────────────────────────────────
    elif stype == "terraria":
        fields.append(_field("アドレス", f"`{info['host']}:{info['port']}`", False))
        if online:
            fields.append(_field("レイテンシ", f"{result.get('latency_ms', '—')} ms"))
            if "players" in result:
                p, mp = result.get("players", 0), result.get("max_players", 0)
                fields.append(_field("プレイヤー", f"{p} / {mp}  {_player_bar(p, mp)}"))
            if result.get("world"):
                fields.append(_field("ワールド", result["world"]))
        else:
            fields.append(_field("エラー", result.get("error", "接続不可"), False))

    # ─── VRChat ──────────────────────────────────────────────
    elif stype == "vrchat":
        fields.append(_field("World ID", f"`{info['host']}`", False))
        if online:
            fields.append(_field("ワールド名", result.get("world_name", "—"), False))
            fields.append(_field("作者", result.get("author", "—")))
            fields.append(_field("容量", str(result.get("capacity", "—"))))
            occ = result.get("occupants", 0)
            pub = result.get("public_occupants", 0)
            prv = result.get("private_occupants", 0)
            fields.append(_field("滞在人数", f"{occ} 人 (公開 {pub} / 非公開 {prv})", False))
        else:
            fields.append(_field("エラー", result.get("error", "不明"), False))

    # ─── Web ─────────────────────────────────────────────────
    elif stype == "web":
        fields.append(_field("URL", result.get("url", "—"), False))
        if online:
            fields.append(_field("HTTP", str(result.get("status_code", "—"))))
            fields.append(_field("レイテンシ", f"{result.get('latency_ms', '—')} ms"))
            ct = result.get("content_type", "")
            if ct:
                fields.append(_field("Content-Type", ct[:60]))
        else:
            fields.append(_field("エラー", result.get("error", "接続不可"), False))

    # ─── 汎用 API ────────────────────────────────────────────
    elif stype == "api":
        fields.append(_field("URL", result.get("url", "—"), False))
        if "status_code" in result:
            fields.append(_field("HTTP", str(result["status_code"])))
            fields.append(_field("レイテンシ", f"{result.get('latency_ms', '—')} ms"))
            snippet = result.get("response_snippet", "")
            if snippet:
                fields.append(_field("レスポンス", f"```\n{snippet[:150]}\n```", False))
        else:
            fields.append(_field("エラー", result.get("error", "接続不可"), False))

    # ─── Steam Server List ───────────────────────────────────
    elif stype == "steam_server_list":
        fields.append(_field("アドレス", f"`{result.get('addr', '—')}`", False))
        if online:
            fields.append(_field("サーバー名", result.get("server_name", "—"), False))
            fields.append(_field("ゲーム", result.get("game", "—")))
            fields.append(_field("マップ", result.get("map", "—")))
            p, mp = result.get("players", 0), result.get("max_players", 0)
            fields.append(_field("プレイヤー", f"{p} / {mp}  {_player_bar(p, mp)}"))
            fields.append(_field("VAC", "✅ 有効" if result.get("vac") else "❌ 無効"))
            fields.append(_field("バージョン", result.get("version", "—")))
        else:
            fields.append(_field("エラー", result.get("error", "—"), False))

    # ─── Game Server API ─────────────────────────────────────
    elif stype == "game_server_api":
        fields.append(_field("アドレス", f"`{info['host']}:{info['port']}`", False))
        fields.append(_field("ゲーム", result.get("game", "—")))
        if online:
            if result.get("server_name"):
                fields.append(_field("サーバー名", result["server_name"], False))
            if result.get("map"):
                fields.append(_field("マップ", result["map"]))
            p, mp = result.get("players", 0), result.get("max_players", 0)
            fields.append(_field("プレイヤー", f"{p} / {mp}  {_player_bar(p, mp)}"))
            if result.get("latency_ms", -1) >= 0:
                fields.append(_field("レイテンシ", f"{result['latency_ms']} ms"))
        else:
            fields.append(_field("エラー", result.get("error", "接続不可"), False))

    # ─── AWS ─────────────────────────────────────────────────
    elif stype == "aws":
        region = result.get("region", info.get("host", "—"))
        fields.append(_field("リージョン", region, False))
        if online:
            ec = result.get("event_count", 0)
            fields.append(_field("アクティブイベント", str(ec)))
            for ev in result.get("active_events", []):
                svc  = ev.get("service", "")
                summ = ev.get("summary", "")[:80]
                st   = ev.get("status", "")
                fields.append(_field(f"🚨 {svc} ({st})", summ, False))
            if ec == 0:
                fields.append(_field("状態", "✅ 全サービス正常", False))
        if result.get("note"):
            fields.append(_field("備考", result["note"], False))
        if result.get("error"):
            fields.append(_field("警告", result["error"], False))

    # ─── Cloudflare ──────────────────────────────────────────
    elif stype == "cloudflare":
        fields.append(_field("全体ステータス", result.get("overall_status", "—"), False))
        if result.get("zone_name"):
            fields.append(_field("ゾーン", result["zone_name"]))
            fields.append(_field("ゾーン状態", result.get("zone_status", "—")))
        for inc in result.get("active_incidents", []):
            fields.append(_field(
                f"🚨 {inc.get('name', '')} [{inc.get('impact', '')}]",
                inc.get("status", "")[:60], False
            ))
        degraded = result.get("degraded_components", [])
        if degraded:
            fields.append(_field("障害コンポーネント", "\n".join(degraded), False))
        elif result.get("healthy"):
            fields.append(_field("状態", "✅ 全コンポーネント正常", False))
        if result.get("error"):
            fields.append(_field("エラー", result["error"], False))

    footer_parts = [f"種別: {stype.upper()}"]
    if info.get("host"):
        footer_parts.append(f"host: {info['host']}")
    footer_parts.append(_now())

    return {
        "title": f"{icon} {status_icon} {label}",
        "color": color,
        "fields": fields,
        "footer": {"text": "  •  ".join(footer_parts)},
    }


def _player_bar(current: int, maximum: int, width: int = 8) -> str:
    """プレイヤー数の視覚的バー"""
    if maximum <= 0:
        return ""
    filled = round(width * current / maximum)
    return "█" * filled + "░" * (width - filled)
