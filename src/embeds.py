"""
embeds.py  –  サーバー種別ごとの Discord Embed 生成
Multilingual support: ja / en / ko / zh
"""

from __future__ import annotations
from datetime import datetime, timezone

from i18n import t, DEFAULT_LOCALE


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

COLOR_OK   = 0x2ECC71
COLOR_WARN = 0xF39C12
COLOR_ERR  = 0xE74C3C


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _field(name: str, value: str, inline: bool = True) -> dict:
    return {"name": name, "value": str(value) or "—", "inline": inline}


def _load_locale() -> str:
    """lang.json からロケールを読み込む（循環 import 回避のためここで import）。"""
    import json
    from pathlib import Path
    lang_path = Path(__file__).parent.parent / "config" / "lang.json"
    try:
        with open(lang_path, encoding="utf-8") as f:
            return json.load(f).get("locale", DEFAULT_LOCALE)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_LOCALE


def build_embed(server_key: str, info: dict, result: dict) -> dict:
    locale = _load_locale()

    def L(key: str, **kwargs) -> str:
        return t(key, locale, **kwargs)

    label  = info.get("label", server_key)
    stype  = result.get("type", info.get("type", ""))
    icon   = ICONS.get(stype, "🖥️")
    online = result.get("online", False)

    # ステータスアイコン & カラー
    if stype in ("aws", "cloudflare"):
        healthy     = result.get("healthy", online)
        status_icon = "🟢" if healthy else ("🟡" if online else "🔴")
        color       = COLOR_OK if healthy else (COLOR_WARN if online else COLOR_ERR)
    else:
        status_icon = "🟢" if online else "🔴"
        color       = COLOR_OK if online else COLOR_ERR

    fields: list[dict] = []
    unavailable = L("embed_unavailable")

    # ─── ゲームサーバー共通 (A2S) ─────────────────────────────
    if stype in ("ark", "valheim", "rust", "cs2", "csgo", "palworld", "7dtd", "steam_query"):
        fields.append(_field(L("embed_address"), f"`{info['host']}:{info['port']}`", False))
        if online:
            fields.append(_field(L("embed_latency"), f"{result.get('latency_ms', '—')} ms"))
            if "server_name" in result:
                fields.append(_field(L("embed_server_name"), result["server_name"], False))
                fields.append(_field(L("embed_map"), result.get("map", "—")))
                p, mp = result.get("players", 0), result.get("max_players", 0)
                fields.append(_field(L("embed_players"), f"{p} / {mp}  {_player_bar(p, mp)}"))
                if result.get("bots", 0):
                    fields.append(_field(L("embed_bots"), str(result["bots"])))
        else:
            fields.append(_field(L("embed_error"), result.get("error", unavailable), False))

    # ─── Minecraft ───────────────────────────────────────────
    elif stype == "minecraft":
        fields.append(_field(L("embed_address"), f"`{info['host']}:{info['port']}`", False))
        if online:
            fields.append(_field(L("embed_version"), result.get("version", "—")))
            fields.append(_field(L("embed_latency"), f"{result.get('latency_ms', '—')} ms"))
            p, mp = result.get("players", 0), result.get("max_players", 0)
            fields.append(_field(L("embed_players"), f"{p} / {mp}  {_player_bar(p, mp)}"))
            if result.get("motd"):
                fields.append(_field(L("embed_motd"), result["motd"][:100], False))
        else:
            fields.append(_field(L("embed_error"), result.get("error", unavailable), False))

    # ─── Terraria ────────────────────────────────────────────
    elif stype == "terraria":
        fields.append(_field(L("embed_address"), f"`{info['host']}:{info['port']}`", False))
        if online:
            fields.append(_field(L("embed_latency"), f"{result.get('latency_ms', '—')} ms"))
            if "players" in result:
                p, mp = result.get("players", 0), result.get("max_players", 0)
                fields.append(_field(L("embed_players"), f"{p} / {mp}  {_player_bar(p, mp)}"))
            if result.get("world"):
                fields.append(_field(L("embed_world"), result["world"]))
        else:
            fields.append(_field(L("embed_error"), result.get("error", unavailable), False))

    # ─── VRChat ──────────────────────────────────────────────
    elif stype == "vrchat":
        fields.append(_field(L("embed_world_id"), f"`{info['host']}`", False))
        if online:
            fields.append(_field(L("embed_world_name"), result.get("world_name", "—"), False))
            fields.append(_field(L("embed_author"),     result.get("author", "—")))
            fields.append(_field(L("embed_capacity"),   str(result.get("capacity", "—"))))
            occ = result.get("occupants", 0)
            pub = result.get("public_occupants", 0)
            prv = result.get("private_occupants", 0)
            fields.append(_field(
                L("embed_occupants"),
                L("embed_occupants_detail", occ=occ, pub=pub, prv=prv),
                False,
            ))
        else:
            fields.append(_field(L("embed_error"), result.get("error", L("embed_unknown")), False))

    # ─── Web ─────────────────────────────────────────────────
    elif stype == "web":
        fields.append(_field("URL", result.get("url", "—"), False))
        if online:
            fields.append(_field(L("embed_http"),         str(result.get("status_code", "—"))))
            fields.append(_field(L("embed_latency"),      f"{result.get('latency_ms', '—')} ms"))
            ct = result.get("content_type", "")
            if ct:
                fields.append(_field(L("embed_content_type"), ct[:60]))
        else:
            fields.append(_field(L("embed_error"), result.get("error", unavailable), False))

    # ─── 汎用 API ────────────────────────────────────────────
    elif stype == "api":
        fields.append(_field("URL", result.get("url", "—"), False))
        if "status_code" in result:
            fields.append(_field(L("embed_http"),    str(result["status_code"])))
            fields.append(_field(L("embed_latency"), f"{result.get('latency_ms', '—')} ms"))
            snippet = result.get("response_snippet", "")
            if snippet:
                fields.append(_field(L("embed_response"), f"```\n{snippet[:150]}\n```", False))
        else:
            fields.append(_field(L("embed_error"), result.get("error", unavailable), False))

    # ─── Steam Server List ───────────────────────────────────
    elif stype == "steam_server_list":
        fields.append(_field(L("embed_address"), f"`{result.get('addr', '—')}`", False))
        if online:
            fields.append(_field(L("embed_server_name"), result.get("server_name", "—"), False))
            fields.append(_field(L("embed_game"),    result.get("game", "—")))
            fields.append(_field(L("embed_map"),     result.get("map", "—")))
            p, mp = result.get("players", 0), result.get("max_players", 0)
            fields.append(_field(L("embed_players"), f"{p} / {mp}  {_player_bar(p, mp)}"))
            fields.append(_field(
                L("embed_vac"),
                L("embed_vac_enabled") if result.get("vac") else L("embed_vac_disabled"),
            ))
            fields.append(_field(L("embed_version"), result.get("version", "—")))
        else:
            fields.append(_field(L("embed_error"), result.get("error", "—"), False))

    # ─── Game Server API ─────────────────────────────────────
    elif stype == "game_server_api":
        fields.append(_field(L("embed_address"), f"`{info['host']}:{info['port']}`", False))
        fields.append(_field(L("embed_game"), result.get("game", "—")))
        if online:
            if result.get("server_name"):
                fields.append(_field(L("embed_server_name"), result["server_name"], False))
            if result.get("map"):
                fields.append(_field(L("embed_map"), result["map"]))
            p, mp = result.get("players", 0), result.get("max_players", 0)
            fields.append(_field(L("embed_players"), f"{p} / {mp}  {_player_bar(p, mp)}"))
            if result.get("latency_ms", -1) >= 0:
                fields.append(_field(L("embed_latency"), f"{result['latency_ms']} ms"))
        else:
            fields.append(_field(L("embed_error"), result.get("error", unavailable), False))

    # ─── AWS ─────────────────────────────────────────────────
    elif stype == "aws":
        region = result.get("region", info.get("host", "—"))
        fields.append(_field(L("embed_region"), region, False))
        if online:
            ec = result.get("event_count", 0)
            fields.append(_field(L("embed_active_events"), str(ec)))
            for ev in result.get("active_events", []):
                svc  = ev.get("service", "")
                summ = ev.get("summary", "")[:80]
                st   = ev.get("status", "")
                fields.append(_field(f"🚨 {svc} ({st})", summ, False))
            if ec == 0:
                fields.append(_field(L("embed_state"), L("embed_all_ok"), False))
        if result.get("note"):
            fields.append(_field(L("embed_note"), result["note"], False))
        if result.get("error"):
            fields.append(_field(L("embed_warning"), result["error"], False))

    # ─── Cloudflare ──────────────────────────────────────────
    elif stype == "cloudflare":
        fields.append(_field(L("embed_overall_status"), result.get("overall_status", "—"), False))
        if result.get("zone_name"):
            fields.append(_field(L("embed_zone"),        result["zone_name"]))
            fields.append(_field(L("embed_zone_status"), result.get("zone_status", "—")))
        for inc in result.get("active_incidents", []):
            fields.append(_field(
                f"🚨 {inc.get('name', '')} [{inc.get('impact', '')}]",
                inc.get("status", "")[:60], False,
            ))
        degraded = result.get("degraded_components", [])
        if degraded:
            fields.append(_field(L("embed_degraded"), "\n".join(degraded), False))
        elif result.get("healthy"):
            fields.append(_field(L("embed_state"), L("embed_cf_all_ok"), False))
        if result.get("error"):
            fields.append(_field(L("embed_error"), result["error"], False))

    footer_parts = [L("embed_type_footer", type=stype.upper())]
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
    if maximum <= 0:
        return ""
    filled = round(width * current / maximum)
    return "█" * filled + "░" * (width - filled)
