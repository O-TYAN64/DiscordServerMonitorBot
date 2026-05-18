"""
bot.py  –  Discord Server Monitor Bot  (v2)
スラッシュコマンドで GitHub Actions のステータスチェックをトリガーする。
"""

import json
import os
from pathlib import Path

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from checkers import SUPPORTED_TYPES

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GITHUB_TOKEN  = os.environ["GITHUB_TOKEN"]
GITHUB_OWNER  = os.environ["GITHUB_OWNER"]
GITHUB_REPO   = os.environ["GITHUB_REPO"]

SERVERS_JSON  = Path(__file__).parent.parent / "config" / "servers.json"

intents = discord.Intents.default()
bot  = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ─── ヘルパー ──────────────────────────────────────────────────

def load_servers() -> dict:
    with open(SERVERS_JSON, encoding="utf-8") as f:
        return json.load(f)

def save_servers(data: dict):
    with open(SERVERS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _default_port(t: str) -> int:
    return {
        "web": 443, "minecraft": 25565, "ark": 7777, "valheim": 2457,
        "rust": 28015, "cs2": 27015, "csgo": 27015, "palworld": 8211,
        "7dtd": 26900, "terraria": 7777, "steam_query": 27015,
        "steam_server_list": 27015, "game_server_api": 27015,
        "vrchat": 0, "aws": 0, "cloudflare": 0, "api": 443,
    }.get(t, 0)

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

@tree.command(name="status", description="サーバーのステータスを確認します")
@app_commands.describe(name="確認したいサーバー名（省略すると全サーバー）")
async def status(interaction: discord.Interaction, name: str = "all"):
    await interaction.response.defer(thinking=True)
    servers = load_servers()

    if name != "all" and name not in servers:
        await interaction.followup.send(
            f"❌ `{name}` は未登録です。\n登録済み: {', '.join(servers) or 'なし'}"
        )
        return

    targets = [name] if name != "all" else list(servers)
    if not targets:
        await interaction.followup.send("⚠️ 登録済みサーバーがありません。`/add_server` で追加してください。")
        return

    ok = await trigger_workflow("check_status.yml", {
        "server_names": ",".join(targets),
        "channel_id": str(interaction.channel_id),
    })
    msg = (
        f"🔍 **{', '.join(targets)}** のチェックをキューに入れました。\n"
        "GitHub Actions の実行後、このチャンネルに結果が届きます。"
        if ok else
        "❌ GitHub Actions のトリガーに失敗しました。Secrets の設定を確認してください。"
    )
    await interaction.followup.send(msg)

# ─── /add_server ──────────────────────────────────────────────

@tree.command(name="add_server", description="監視対象サーバーを追加します")
@app_commands.describe(
    name="識別名",
    type=f"種別: {' / '.join(SUPPORTED_TYPES)}",
    host="ホスト / IP / World ID / AWS リージョン / Cloudflare",
    port="ポート番号（省略時は種別ごとのデフォルト）",
    label="表示名（省略時は識別名）",
    extra="追加オプション JSON (例: {\"game\":\"rust\",\"endpoint\":\"/api/status\"})",
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
            f"❌ 未対応の種別 `{type}` です。\n対応: {', '.join(f'`{t}`' for t in SUPPORTED_TYPES)}"
        )
        return

    servers = load_servers()
    if name in servers:
        await interaction.response.send_message(f"⚠️ `{name}` は既に登録済みです。削除してから追加してください。")
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
            await interaction.response.send_message("❌ `extra` の JSON が不正です。")
            return

    servers[name] = entry
    save_servers(servers)

    embed = discord.Embed(title="✅ サーバー追加完了", color=0x2ECC71)
    embed.add_field(name="識別名", value=name)
    embed.add_field(name="種別", value=type)
    embed.add_field(name="ホスト", value=host)
    embed.add_field(name="ポート", value=str(entry["port"]))
    embed.add_field(name="表示名", value=entry["label"])
    if extra:
        embed.add_field(name="追加設定", value=f"```json\n{extra[:200]}\n```", inline=False)
    await interaction.response.send_message(embed=embed)

# ─── /remove_server ───────────────────────────────────────────

@tree.command(name="remove_server", description="監視対象サーバーを削除します")
@app_commands.describe(name="削除するサーバーの識別名")
async def remove_server(interaction: discord.Interaction, name: str):
    servers = load_servers()
    if name not in servers:
        await interaction.response.send_message(f"❌ `{name}` は未登録です。")
        return
    del servers[name]
    save_servers(servers)
    await interaction.response.send_message(f"🗑️ `{name}` を削除しました。")

# ─── /list_servers ────────────────────────────────────────────

@tree.command(name="list_servers", description="登録済みサーバー一覧を表示します")
async def list_servers(interaction: discord.Interaction):
    servers = load_servers()
    if not servers:
        await interaction.response.send_message("📋 登録済みサーバーはありません。")
        return

    embed = discord.Embed(title="📋 登録済みサーバー一覧", color=0x3498DB)
    for key, info in servers.items():
        host_str = f"`{info['host']}`" + (f":`{info['port']}`" if info.get("port") else "")
        embed.add_field(
            name=f"{info.get('label', key)} (`{key}`)",
            value=f"種別: `{info['type']}`\nHost: {host_str}",
            inline=False,
        )
    await interaction.response.send_message(embed=embed)

# ─── /server_types ────────────────────────────────────────────

@tree.command(name="server_types", description="対応サーバー種別の一覧を表示します")
async def server_types(interaction: discord.Interaction):
    descriptions = {
        "minecraft":         "Minecraft Java Edition (SLP プロトコル)",
        "ark":               "ARK: Survival Evolved/Ascended (Steam A2S)",
        "valheim":           "Valheim (Steam A2S)",
        "rust":              "Rust (Steam A2S)",
        "cs2":               "Counter-Strike 2 / CS:GO (Steam A2S)",
        "csgo":              "CS:GO (cs2 の別名)",
        "palworld":          "Palworld (Steam A2S)",
        "7dtd":              "7 Days to Die (Steam A2S)",
        "terraria":          "Terraria (TCP ping + REST API オプション)",
        "vrchat":            "VRChat ワールド (公式 API)",
        "steam_query":       "Steam A2S 汎用クエリ",
        "web":               "HTTP/HTTPS エンドポイント",
        "api":               "カスタム REST API",
        "steam_server_list": "Steam Web API でサーバー検索",
        "game_server_api":   "Game Server API (api.gameserverapi.com)",
        "aws":               "AWS Health Dashboard",
        "cloudflare":        "Cloudflare Status + Zone API",
    }
    embed = discord.Embed(title="🖥️ 対応サーバー種別", color=0x5865F2)
    for t, desc in descriptions.items():
        embed.add_field(name=f"`{t}`", value=desc, inline=False)
    await interaction.response.send_message(embed=embed)

# ─── Bot 起動 ─────────────────────────────────────────────────

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot ready: {bot.user} (id={bot.user.id})")
    print(f"   対応種別: {', '.join(SUPPORTED_TYPES)}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)