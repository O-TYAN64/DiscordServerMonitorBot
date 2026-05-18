Claudeが応答を完了しました

githubactionsで各サーバーゲームのサーバーを含むサーバーのステータスを確認するdiscordbotを作りたいサーバーの追加も可能で
10:07

どんなサーバーのステータスを監視したいか、もう少し教えてください！

Q: 監視したいサーバーの種類は？（該当するものをすべて選択）
A: 一般的なWebサーバー/API, ARK, vrchat

Q: ステータス確認の方法は？
A: 両方

Q: GitHub Actionsの実行頻度は？
A: コマンド実行の時にメッセージを送る
10:07

わかりました！コマンド実行時にDiscordでステータス確認するBotですね。以下の構成で作ります：

    監視対象: Webサーバー/API、ARK、VRChat
    確認方法: ping（死活）+ 各プロトコルで詳細取得
    トリガー: Discordコマンド → GitHub Actions → 結果をDiscordに返信

では作成します！
Check frontend design skill

全ファイルを作成します。まずプロジェクト構造を設計します：
7個のファイルを作成しました, 2個のコマンドを実行しました, ファイルを読み取りました
完了

全ファイルが揃いました！構成の説明です：
📁 ファイル構成
ファイル	役割
src/bot.py	Discord Bot 本体（スラッシュコマンド受付）
src/check_status.py	ステータスチェッカー（Actions から実行）
config/servers.json	監視サーバーの設定ファイル
.github/workflows/check_status.yml	チェック実行ワークフロー
.github/workflows/run_bot.yml	Bot 起動ワークフロー
🔧 セットアップ手順

① GitHub Secrets に 3 つ追加

    DISCORD_TOKEN … Bot のトークン
    DISCORD_WEBHOOK … 結果投稿先の Webhook URL
    GH_PAT … workflow スコープ付きの Personal Access Token

② リポジトリに push → Actions で Run Discord Bot を手動実行
💬 スラッシュコマンド

/status                        → 全サーバーチェック
/status name:ark1              → 個別チェック
/add_server name:ark1 type:ark host:1.2.3.4 port:7777
/remove_server name:ark1
/list_servers

⚠️ 注意点

    Bot は GitHub Actions で常駐起動しますが、Actions の無料枠（月 2,000 分）を消費します。長期運用にはセルフホストランナーや VPS での起動を検討してください。
    /add_server で追加したサーバーは Actions の一時環境に書き込まれるため、リポジトリに push しないと次回起動時に消えます。永続化が必要な場合は GitHub API で servers.json を直接更新する処理の追加をお勧めします。

Readme
ドキュメント · MD 
Bot
PY 
Check status
PY 
Servers
コード · JSON 
Check status
YML 
Run bot
YML 


Claude は AI のため、誤りを含む可能性があります。回答内容は必ずご確認ください。
Bot · PY
"""
Discord Server Monitor Bot
Receives slash commands and triggers GitHub Actions to check server status.
"""
 
import os
import json
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
 
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_OWNER = os.environ["GITHUB_OWNER"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
 
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
 
 
def load_servers() -> dict:
    """Load servers.json config"""
    path = os.path.join(os.path.dirname(__file__), "..", "config", "servers.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
 
 
def save_servers(data: dict):
    """Save servers.json config"""
    path = os.path.join(os.path.dirname(__file__), "..", "config", "servers.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
 
 
async def trigger_github_action(workflow_id: str, inputs: dict) -> bool:
    """Trigger a GitHub Actions workflow dispatch"""
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow_id}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"ref": "main", "inputs": inputs}
 
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            return resp.status == 204
 
 
# ─────────────────────────────────────────────
# /status  コマンド
# ─────────────────────────────────────────────
@tree.command(name="status", description="サーバーのステータスを確認します")
@app_commands.describe(name="確認したいサーバー名（省略すると全サーバー）")
async def status(interaction: discord.Interaction, name: str = "all"):
    await interaction.response.defer(thinking=True)
 
    servers = load_servers()
 
    if name != "all" and name not in servers:
        await interaction.followup.send(
            f"❌ サーバー `{name}` は登録されていません。\n"
            f"登録済み: {', '.join(servers.keys()) or 'なし'}"
        )
        return
 
    targets = [name] if name != "all" else list(servers.keys())
    if not targets:
        await interaction.followup.send("⚠️ 登録されているサーバーがありません。`/add_server` で追加してください。")
        return
 
    inputs = {
        "server_names": ",".join(targets),
        "channel_id": str(interaction.channel_id),
        "message_id": "0",  # 結果はbotが直接投稿
    }
 
    ok = await trigger_github_action("check_status.yml", inputs)
    if ok:
        await interaction.followup.send(
            f"🔍 **{', '.join(targets)}** のステータス確認をキューに入れました。\n"
            "GitHub Actions が実行され、結果はこのチャンネルに投稿されます。"
        )
    else:
        await interaction.followup.send("❌ GitHub Actions のトリガーに失敗しました。トークンや設定を確認してください。")
 
 
# ─────────────────────────────────────────────
# /add_server  コマンド
# ─────────────────────────────────────────────
@tree.command(name="add_server", description="監視対象のサーバーを追加します")
@app_commands.describe(
    name="サーバーの識別名",
    type="種類: web / ark / vrchat",
    host="ホスト名またはIPアドレス",
    port="ポート番号（省略可）",
    label="表示名（省略可）",
)
async def add_server(
    interaction: discord.Interaction,
    name: str,
    type: str,
    host: str,
    port: int = 0,
    label: str = "",
):
    if type not in ("web", "ark", "vrchat"):
        await interaction.response.send_message("❌ `type` は `web` / `ark` / `vrchat` のいずれかを指定してください。")
        return
 
    servers = load_servers()
    if name in servers:
        await interaction.response.send_message(f"⚠️ `{name}` はすでに登録されています。削除してから追加してください。")
        return
 
    servers[name] = {
        "type": type,
        "host": host,
        "port": port or _default_port(type),
        "label": label or name,
    }
    save_servers(servers)
 
    embed = discord.Embed(title="✅ サーバー追加完了", color=0x2ECC71)
    embed.add_field(name="識別名", value=name)
    embed.add_field(name="種類", value=type)
    embed.add_field(name="ホスト", value=host)
    embed.add_field(name="ポート", value=servers[name]["port"])
    embed.add_field(name="表示名", value=servers[name]["label"])
    await interaction.response.send_message(embed=embed)
 
 
# ─────────────────────────────────────────────
# /remove_server  コマンド
# ─────────────────────────────────────────────
@tree.command(name="remove_server", description="監視対象のサーバーを削除します")
@app_commands.describe(name="削除するサーバーの識別名")
async def remove_server(interaction: discord.Interaction, name: str):
    servers = load_servers()
    if name not in servers:
        await interaction.response.send_message(f"❌ `{name}` は登録されていません。")
        return
 
    del servers[name]
    save_servers(servers)
    await interaction.response.send_message(f"🗑️ `{name}` を削除しました。")
 
 
# ─────────────────────────────────────────────
# /list_servers  コマンド
# ─────────────────────────────────────────────
@tree.command(name="list_servers", description="登録済みサーバー一覧を表示します")
async def list_servers(interaction: discord.Interaction):
    servers = load_servers()
    if not servers:
        await interaction.response.send_message("📋 登録されているサーバーはありません。")
        return
 
    embed = discord.Embed(title="📋 登録済みサーバー一覧", color=0x3498DB)
    for key, info in servers.items():
        embed.add_field(
            name=f"{info['label']} (`{key}`)",
            value=f"種類: `{info['type']}`\nHost: `{info['host']}:{info['port']}`",
            inline=False,
        )
    await interaction.response.send_message(embed=embed)
 
 
# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _default_port(server_type: str) -> int:
    return {"web": 80, "ark": 7777, "vrchat": 0}.get(server_type, 0)
 
 
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot ready: {bot.user} (id={bot.user.id})")
 
 
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
 

