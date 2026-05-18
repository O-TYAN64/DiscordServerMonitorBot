# 🖥️ Discord Server Monitor Bot

Discord のスラッシュコマンドでサーバーのステータスを確認する Bot です。  
コマンドを受け取ると **GitHub Actions** がステータスチェックを実行し、結果を Discord に投稿します。

## 対応サーバー種類

| 種類 | 確認内容 |
|------|----------|
| `web` | HTTP ステータスコード・レイテンシ |
| `ark` | TCP 死活 + UDP A2S_INFO（プレイヤー数・マップ） |
| `vrchat` | VRChat API でワールド情報・滞在人数 |

---

## セットアップ

### 1. Discord Bot の作成

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリを作成
2. **Bot** タブ → トークンをコピー
3. **OAuth2 → URL Generator** で `bot` + `applications.commands` スコープを選択  
   権限: `Send Messages`, `Embed Links`
4. 生成された URL でサーバーに招待

### 2. Discord Webhook の作成

1. 結果を投稿したいチャンネルの **設定 → 連携サービス → Webhook** を作成
2. Webhook URL をコピー

### 3. GitHub Secrets の設定

リポジトリの **Settings → Secrets and variables → Actions** に以下を追加:

| シークレット名 | 内容 |
|----------------|------|
| `DISCORD_TOKEN` | Discord Bot トークン |
| `DISCORD_WEBHOOK` | Discord Webhook URL |
| `GH_PAT` | GitHub Personal Access Token (`workflow` スコープ必須) |

### 4. GitHub Actions の有効化

リポジトリを push した後、**Actions** タブで `Run Discord Bot` ワークフローを手動実行します。

> ⚠️ GitHub Actions の無料枠はパブリックリポジトリは無制限、プライベートは月 2,000 分です。

---

## 使い方

| コマンド | 説明 |
|----------|------|
| `/status` | 全サーバーのステータスを確認 |
| `/status name:サーバー名` | 指定サーバーのステータスを確認 |
| `/add_server name:識別名 type:種類 host:ホスト port:ポート` | サーバーを追加 |
| `/remove_server name:識別名` | サーバーを削除 |
| `/list_servers` | 登録済みサーバー一覧を表示 |

### サーバー追加の例

```
# Web サーバー
/add_server name:mysite type:web host:example.com port:443 label:自分のサイト

# ARK サーバー
/add_server name:ark1 type:ark host:192.168.1.100 port:7777 label:ARKサーバー

# VRChat ワールド (host に World ID を入力)
/add_server name:vrc1 type:vrchat host:wrld_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx label:私のワールド
```

---

## ファイル構成

```
discord-server-monitor/
├── .github/workflows/
│   ├── check_status.yml   # ステータスチェック (workflow_dispatch)
│   └── run_bot.yml        # Discord Bot の常駐起動
├── src/
│   ├── bot.py             # Discord Bot (スラッシュコマンド)
│   └── check_status.py    # ステータスチェッカー (Actions から呼ばれる)
├── config/
│   └── servers.json       # 監視サーバー設定
└── requirements.txt
```

---

## 仕組み

```
Discord ユーザー
    │  /status コマンド
    ▼
Discord Bot (bot.py)
    │  GitHub API で workflow_dispatch をトリガー
    ▼
GitHub Actions (check_status.yml)
    │  check_status.py を実行
    ▼
各サーバーへの接続チェック
    │  結果を Discord Webhook で投稿
    ▼
Discord チャンネルに Embed で結果表示
```

## 注意事項

- `/add_server` でサーバーを追加すると `config/servers.json` がローカルに書き込まれます。  
  GitHub Actions 環境は一時的なので、**永続化したい場合はリポジトリに push するか、外部ストレージ（Gist, S3 等）を使用してください。**
- VRChat の World ID は `wrld_` で始まる UUID です。VRChat のワールドページ URL から確認できます。
- ARK の A2S_INFO クエリはサーバー側でクエリポートが開放されている必要があります（デフォルトはゲームポートと同一）。
