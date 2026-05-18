# 🖥️ Discord Server Monitor Bot  v2

Discord スラッシュコマンドでサーバーのステータスを確認する Bot です。  
コマンドを受け取ると **GitHub Actions** がチェックを実行し、結果を Discord に Embed で投稿します。

## 対応サーバー種別

| 種別 | 確認内容 |
|------|----------|
| `minecraft` | SLP プロトコル（バージョン・MOTD・プレイヤー数） |
| `ark` | Steam A2S（マップ・プレイヤー数） |
| `valheim` | Steam A2S |
| `rust` | Steam A2S |
| `cs2` / `csgo` | Steam A2S |
| `palworld` | Steam A2S |
| `7dtd` | Steam A2S |
| `terraria` | TCP ping + REST API (tModLoader) |
| `vrchat` | VRChat 公式 API（ワールド・滞在人数） |
| `steam_query` | Steam A2S 汎用 |
| `web` | HTTP/HTTPS ステータスコード・レイテンシ |
| `api` | カスタム REST エンドポイント |
| `steam_server_list` | Steam Web API でサーバー情報取得 |
| `game_server_api` | api.gameserverapi.com 汎用 API |
| `aws` | AWS Health Dashboard |
| `cloudflare` | Cloudflare Status + Zone API |

---

## セットアップ

### 1. Discord Bot の作成

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリを作成
2. **Bot** タブ → トークンをコピー
3. **OAuth2 → URL Generator** で `bot` + `applications.commands` を選択
4. 権限: `Send Messages`, `Embed Links` を付与してサーバーに招待

### 2. Discord Webhook の作成

結果を投稿したいチャンネルで **設定 → 連携サービス → Webhook** を作成し URL をコピー

### 3. GitHub Secrets の設定

| シークレット名 | 必須 | 内容 |
|----------------|------|------|
| `DISCORD_TOKEN` | ✅ | Discord Bot トークン |
| `DISCORD_WEBHOOK` | ✅ | Discord Webhook URL |
| `GH_PAT` | ✅ | GitHub PAT (`workflow` スコープ) |
| `STEAM_API_KEY` | ☑️ | Steam Web API キー (`steam_server_list` 種別) |
| `GAME_SERVER_API_KEY` | ☑️ | Game Server API キー |
| `CF_API_KEY` | ☑️ | Cloudflare API キー (ゾーン確認) |
| `CF_ZONE_ID` | ☑️ | Cloudflare Zone ID |

---

## スラッシュコマンド

| コマンド | 説明 |
|----------|------|
| `/status` | 全サーバーのステータスを確認 |
| `/status name:識別名` | 指定サーバーのステータスを確認 |
| `/add_server name:識別名 type:種別 host:ホスト` | サーバーを追加 |
| `/remove_server name:識別名` | サーバーを削除 |
| `/list_servers` | 登録済みサーバー一覧 |
| `/server_types` | 対応種別一覧を表示 |

### サーバー追加例

```
# Minecraft
/add_server name:mc1 type:minecraft host:mc.example.com port:25565 label:自分のMC

# ARK
/add_server name:ark1 type:ark host:192.168.1.100 port:7777

# Steam Web API でサーバー取得
/add_server name:rust1 type:steam_server_list host:1.2.3.4 port:28015

# Game Server API
/add_server name:rust2 type:game_server_api host:1.2.3.4 port:28015 extra:{"game":"rust"}

# カスタム REST API (expect_key/expect_value でオンライン判定)
/add_server name:myapi type:api host:https://myserver.com endpoint:/api/health extra:{"expect_key":"status","expect_value":"ok"}

# AWS 東京リージョン
/add_server name:aws_tokyo type:aws host:ap-northeast-1 extra:{"services":"ec2,rds,s3"}

# Cloudflare + Zone 確認
/add_server name:cf type:cloudflare host:global extra:{"cf_zone_id":"your_zone_id"}

# Terraria (REST API 有効)
/add_server name:terra type:terraria host:1.2.3.4 port:7777 extra:{"rest_port":7878}
```

---

## ファイル構成

```
discord-server-monitor/
├── .github/workflows/
│   ├── check_status.yml   # ステータスチェック (workflow_dispatch)
│   └── run_bot.yml        # Discord Bot 起動
├── src/
│   ├── bot.py             # Discord Bot
│   ├── checkers.py        # 全サーバー種別チェッカー
│   ├── embeds.py          # Discord Embed 生成
│   └── check_status.py    # Actions エントリポイント
├── config/
│   └── servers.json       # 監視サーバー設定
└── requirements.txt
```

## 仕組み

```
Discord ユーザー (/status)
       │
       ▼
bot.py (GitHub Actions workflow_dispatch をトリガー)
       │
       ▼
check_status.yml (GitHub Actions)
       │
       ▼
checkers.py (種別ごとのチェック実行)
  ├─ Minecraft SLP
  ├─ Steam A2S (ARK/Valheim/Rust/CS2/Palworld/7DTD)
  ├─ VRChat API
  ├─ Steam Web API
  ├─ Game Server API
  ├─ AWS Health API
  ├─ Cloudflare Status API
  └─ HTTP/REST チェック
       │
       ▼
embeds.py (Discord Embed 生成)
       │
       ▼
Discord Webhook → チャンネルに結果投稿
```