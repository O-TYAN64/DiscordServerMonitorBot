"""
bot.py  –  Discord Server Monitor Bot  (v2)
スラッシュコマンドで GitHub Actions のステータスチェックをトリガーする。
Multilingual support: ja / en / ko / zh
"""

import json
import os
from pathlib import Path

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from checkers import SUPPORTED_TYPES
from i18n import t, SUPPORTED_LOCALES, DEFAULT_LOCALE

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GITHUB_TOKEN  = os.environ["GITHUB_TOKEN"]
GITHUB_OWNER  = os.environ["GITHUB_OWNER"]
GITHUB_REPO   = os.environ["GITHUB_REPO"]

SERVERS_JSON  = Path(__file__).parent.parent / "config" / "servers.json"
LANG_JSON     = Path(__file__).parent.parent / "config" / "lang.json"

intents = discord.Intents.default()
bot  = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ─── 言語設定 ──────────────────────────────────────────────────

def load_lang() -> str:
    """config/lang.json からサーバーの表示言語を読み込む。"""
    try:
        with open(LANG_JSON, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("locale", DEFAULT_LOCALE)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_LOCALE

def save_lang(locale: str):
    LANG_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(LANG_JSON, "w", encoding="utf-8") as f:
        json.dump({"locale": locale}, f, ensure_ascii=False, indent=2)

def L(key: str, **kwargs) -> str:
    """現在のサーバー言語で翻訳文字列を返す。"""
    return t(key, load_lang(), **kwargs)

# ─── ヘルパー ──────────────────────────────────────────────────

def load_servers() -> dict:
    with open(SERVERS_JSON, encoding="utf-8") as f:
        return json.load(f)

def save_servers(data: dict):
    with open(SERVERS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _default_port(t_: str) -> int:
    return {
        "web": 443, "minecraft": 25565, "ark": 7777, "valheim": 2457,
        "rust": 28015, "cs2": 27015, "csgo": 27015, "palworld": 8211,
        "7dtd": 26900, "terraria": 7777, "steam_query": 27015,
        "steam_server_list": 27015, "game_server_api": 27015,
        "vrchat": 0, "aws": 0, "cloudflare": 0, "api": 443,
    }.get(t_, 0)

async def trigger_workflow(workflow: str, inputs: dict) -> bool:
    url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/actions/workflows/{workflow}/dispatches"
    )
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(url, headers=headers, json={"ref": "main", "inputs": inputs}) as r:
            return r.status == 204

# ─── /status ──────────────────────────────────────────────────

@tree.command(name="status", description="Check server status / サーバーのステータスを確認 / 서버 상태 확인 / 检查服务器状态")
@app_commands.describe(name="Server name to check (omit for all) / 確認したいサーバー名（省略すると全サーバー）")
async def status(interaction: discord.Interaction, name: str = "all"):
    await interaction.response.defer(thinking=True)
    servers = load_servers()

    if name != "all" and name not in servers:
        await interaction.followup.send(
            L("status_not_registered", name=name, list=", ".join(servers) or "—")
        )
        return

    targets = [name] if name != "all" else list(servers)
    if not targets:
        await interaction.followup.send(L("status_none_registered"))
        return

    ok = await trigger_workflow("check_status.yml", {
        "server_names": ",".join(targets),
        "channel_id": str(interaction.channel_id),
    })
    msg = (
        L("status_queued", targets=", ".join(targets))
        if ok else
        L("status_trigger_failed")
    )
    await interaction.followup.send(msg)

# ─── /add_server ──────────────────────────────────────────────

@tree.command(name="add_server", description="Add a server to monitor / 監視対象サーバーを追加 / 서버 추가 / 添加服务器")
@app_commands.describe(
    name="Identifier / 識別名",
    type="Server type / 種別",
    host="Host / IP / World ID / AWS region",
    port="Port (optional) / ポート番号（任意）",
    label="Display name (optional) / 表示名（任意）",
    extra='Extra options JSON / 追加オプション JSON (e.g. {"game":"rust"})',
)
async def add_server(
    interaction: discord.Interaction,
    name: str,
    type: str,
    host: str,
    port: int = -1,
    label: str = "",
    extra: str = "",
):
    if type not in SUPPORTED_TYPES:
        await interaction.response.send_message(
            L("add_unsupported_type", type=type, list=", ".join(f"`{t_}`" for t_ in SUPPORTED_TYPES))
        )
        return

    servers = load_servers()
    if name in servers:
        await interaction.response.send_message(L("add_already_exists", name=name))
        return

    entry: dict = {
        "type": type,
        "host": host,
        "port": port if port >= 0 else _default_port(type),
        "label": label or name,
    }

    if extra:
        try:
            entry.update(json.loads(extra))
        except json.JSONDecodeError:
            await interaction.response.send_message(L("add_invalid_json"))
            return

    servers[name] = entry
    save_servers(servers)

    embed = discord.Embed(title=L("add_success_title"), color=0x2ECC71)
    embed.add_field(name=L("field_identifier"), value=name)
    embed.add_field(name=L("field_type"),       value=type)
    embed.add_field(name=L("field_host"),       value=host)
    embed.add_field(name=L("field_port"),       value=str(entry["port"]))
    embed.add_field(name=L("field_label"),      value=entry["label"])
    if extra:
        embed.add_field(name=L("field_extra"), value=f"```json\n{extra[:200]}\n```", inline=False)
    await interaction.response.send_message(embed=embed)

# ─── /remove_server ───────────────────────────────────────────

@tree.command(name="remove_server", description="Remove a monitored server / 監視対象サーバーを削除 / 서버 삭제 / 删除服务器")
@app_commands.describe(name="Identifier of the server to remove / 削除するサーバーの識別名")
async def remove_server(interaction: discord.Interaction, name: str):
    servers = load_servers()
    if name not in servers:
        await interaction.response.send_message(L("remove_not_found", name=name))
        return
    del servers[name]
    save_servers(servers)
    await interaction.response.send_message(L("remove_success", name=name))

# ─── /list_servers ────────────────────────────────────────────

@tree.command(name="list_servers", description="Show registered servers / 登録済みサーバー一覧 / 서버 목록 / 服务器列表")
async def list_servers(interaction: discord.Interaction):
    servers = load_servers()
    if not servers:
        await interaction.response.send_message(L("list_none"))
        return

    embed = discord.Embed(title=L("list_title"), color=0x3498DB)
    for key, info in servers.items():
        host_str = f"`{info['host']}`" + (f":`{info['port']}`" if info.get("port") else "")
        embed.add_field(
            name=f"{info.get('label', key)} (`{key}`)",
            value=L("list_field_type_host", type=info["type"], host=host_str),
            inline=False,
        )
    await interaction.response.send_message(embed=embed)

# ─── /server_types ────────────────────────────────────────────

@tree.command(name="server_types", description="Show supported server types / 対応種別一覧 / 지원 유형 목록 / 支持类型列表")
async def server_types(interaction: discord.Interaction):
    type_keys = [
        "minecraft", "ark", "valheim", "rust", "cs2", "csgo",
        "palworld", "7dtd", "terraria", "vrchat", "steam_query",
        "web", "api", "steam_server_list", "game_server_api", "aws", "cloudflare",
    ]
    embed = discord.Embed(title=L("types_title"), color=0x5865F2)
    for type_key in type_keys:
        embed.add_field(name=f"`{type_key}`", value=L(f"type_desc_{type_key}"), inline=False)
    await interaction.response.send_message(embed=embed)

# ─── /set_language ────────────────────────────────────────────

@tree.command(name="set_language", description="Set Bot language / Bot言語設定 / Bot 언어 설정 / 设置Bot语言")
@app_commands.describe(locale="ja / en / ko / zh")
async def set_language(interaction: discord.Interaction, locale: str):
    if locale not in SUPPORTED_LOCALES:
        await interaction.response.send_message(
            t("setlang_invalid", load_lang())
        )
        return
    save_lang(locale)
    await interaction.response.send_message(t("setlang_success", locale))

# ─── Bot 起動 ─────────────────────────────────────────────────

@bot.event
async def on_ready():
    await tree.sync()
    locale = load_lang()
    print(f"✅ Bot ready: {bot.user} (id={bot.user.id})  lang={locale}")
    print(f"   Supported types: {', '.join(SUPPORTED_TYPES)}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)