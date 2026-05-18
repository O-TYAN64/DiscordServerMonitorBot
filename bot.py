"""
VRChat Discord Bot
  /vrc status   … VRChatサーバーの死活確認
  /vrc world    … ワールド検索
"""

import os
import re
import base64
import urllib.parse
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

# ── 設定 ──────────────────────────────────────────────────────────────────────

DISCORD_TOKEN  = os.environ["DISCORD_TOKEN"]
VRC_USERNAME   = os.environ["VRC_USERNAME"]   # VRChatのユーザー名
VRC_PASSWORD   = os.environ["VRC_PASSWORD"]   # VRChatのパスワード

VRC_API        = "https://api.vrchat.cloud/api/1"
VRC_STATUS_URL = "https://status.vrchat.com/api/v2/summary.json"

# VRChat が要求する User-Agent（アプリ名/バージョン contact:メールアドレス）
USER_AGENT = "VRChatDiscordBot/1.0.0 contact:your-email@example.com"

# ── Discord Bot セットアップ ──────────────────────────────────────────────────

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ── VRChat 認証ヘルパー ───────────────────────────────────────────────────────

def _basic_auth_header() -> str:
    """Basic認証ヘッダー用 base64 文字列を生成"""
    encoded_user = urllib.parse.quote(VRC_USERNAME, safe="")
    encoded_pass = urllib.parse.quote(VRC_PASSWORD, safe="")
    token = base64.b64encode(f"{encoded_user}:{encoded_pass}".encode()).decode()
    return f"Basic {token}"


async def vrchat_login(session: aiohttp.ClientSession) -> str | None:
    """
    VRChat API にログインして auth クッキーを返す。
    ⚠ セッション上限があるため、毎回ログインせず auth クッキーを再利用してください。
    """
    headers = {
        "Authorization": _basic_auth_header(),
        "User-Agent": USER_AGENT,
    }
    async with session.get(f"{VRC_API}/auth/user", headers=headers) as resp:
        if resp.status == 200:
            cookies = session.cookie_jar.filter_cookies(VRC_API)
            auth_cookie = cookies.get("auth")
            return auth_cookie.value if auth_cookie else None
        return None


def _vrc_headers() -> dict:
    return {"User-Agent": USER_AGENT}

# ── /vrc コマンドグループ ────────────────────────────────────────────────────

vrc_group = app_commands.Group(name="vrc", description="VRChat 関連コマンド")


# ── /vrc status ──────────────────────────────────────────────────────────────

@vrc_group.command(name="status", description="VRChatサーバーの稼働状況を確認します")
async def vrc_status(interaction: discord.Interaction):
    await interaction.response.defer()

    async with aiohttp.ClientSession() as session:
        # 公式ステータスページ（Statuspage.io）から取得
        try:
            async with session.get(VRC_STATUS_URL, headers=_vrc_headers()) as resp:
                data = await resp.json()
        except Exception as e:
            await interaction.followup.send(f"❌ ステータス取得に失敗しました: {e}")
            return

    overall = data.get("status", {})
    indicator = overall.get("indicator", "unknown")  # none / minor / major / critical
    description = overall.get("description", "不明")

    # インジケーターをアイコンに変換
    icon_map = {
        "none":     ("🟢", 0x57F287),  # 正常
        "minor":    ("🟡", 0xFEE75C),  # 軽微な障害
        "major":    ("🟠", 0xFF8C00),  # 大きな障害
        "critical": ("🔴", 0xED4245),  # 深刻な障害
    }
    icon, color = icon_map.get(indicator, ("⚪", 0x99AAB5))

    # コンポーネント別ステータス
    components = data.get("components", [])
    fields = []
    for comp in components:
        comp_status = comp.get("status", "unknown")
        comp_icon = "🟢" if comp_status == "operational" else "🔴"
        fields.append({
            "name": comp.get("name", "Unknown"),
            "value": f"{comp_icon} {comp_status}",
            "inline": True,
        })

    embed = discord.Embed(
        title=f"{icon} VRChat サーバーステータス",
        description=description,
        color=color,
        url="https://status.vrchat.com/",
    )
    for f in fields[:25]:  # Embed フィールド上限は 25
        embed.add_field(name=f["name"], value=f["value"], inline=f["inline"])

    await interaction.followup.send(embed=embed)


# ── /vrc world ───────────────────────────────────────────────────────────────

@vrc_group.command(name="world", description="VRChatのワールドを検索します")
@app_commands.describe(
    query="検索キーワード",
    count="取得件数（1〜10、デフォルト5）",
)
async def vrc_world(
    interaction: discord.Interaction,
    query: str,
    count: app_commands.Range[int, 1, 10] = 5,
):
    await interaction.response.defer()

    async with aiohttp.ClientSession() as session:
        # ログイン
        auth_cookie = await vrchat_login(session)
        if not auth_cookie:
            await interaction.followup.send(
                "❌ VRChat へのログインに失敗しました。`VRC_USERNAME` / `VRC_PASSWORD` を確認してください。"
            )
            return

        # ワールド検索
        params = {
            "search": query,
            "n":      count,
            "sort":   "popularity",
            "order":  "descending",
        }
        headers = {**_vrc_headers(), "Cookie": f"auth={auth_cookie}"}
        try:
            async with session.get(
                f"{VRC_API}/worlds", params=params, headers=headers
            ) as resp:
                if resp.status == 401:
                    await interaction.followup.send("❌ VRChat API の認証に失敗しました。")
                    return
                worlds = await resp.json()
        except Exception as e:
            await interaction.followup.send(f"❌ ワールド検索に失敗しました: {e}")
            return

    if not worlds:
        await interaction.followup.send(f"「{query}」に一致するワールドが見つかりませんでした。")
        return

    embed = discord.Embed(
        title=f"🌐 ワールド検索: {query}",
        color=0x5865F2,
    )

    for w in worlds[:count]:
        capacity   = w.get("capacity", "?")
        visits     = f"{w.get('visits', 0):,}"
        world_id   = w.get("id", "")
        author     = w.get("authorName", "不明")

        embed.add_field(
            name=w.get("name", "（名前なし）"),
            value=(
                f"👤 作者: {author}\n"
                f"🧑‍🤝‍🧑 定員: {capacity} 人\n"
                f"👣 訪問数: {visits}\n"
                f"🔗 [VRChatで開く](https://vrchat.com/home/world/{world_id})"
            ),
            inline=False,
        )

    await interaction.followup.send(embed=embed)


# ── Bot 起動 ─────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    bot.tree.add_command(vrc_group)
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")


bot.run(DISCORD_TOKEN)
