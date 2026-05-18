# Discord Bot

GitHub Actions で自動デプロイされる Discord Bot のひな形です。

## セットアップ

### 1. Discord Bot トークンの取得

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」でアプリを作成
3. 「Bot」タブ → 「Reset Token」でトークンを取得
4. 「Privileged Gateway Intents」の `MESSAGE CONTENT INTENT` を有効化

### 2. GitHub Secrets の設定

リポジトリの `Settings > Secrets and variables > Actions` に追加:

| Secret 名 | 内容 |
|---|---|
| `DISCORD_TOKEN` | Discord Bot のトークン |
| `SERVER_HOST` | デプロイ先サーバーのホスト (SSH デプロイ時) |
| `SERVER_USER` | SSH ユーザー名 |
| `SERVER_SSH_KEY` | SSH 秘密鍵 |

### 3. ローカル開発

```bash
cp .env.example .env
# .env に DISCORD_TOKEN を記入

npm install
npm run dev
```

## GitHub Actions ワークフロー

| ファイル | トリガー | 内容 |
|---|---|---|
| `ci.yml` | PR 作成時 | テスト実行 |
| `deploy.yml` | main へのプッシュ | テスト → デプロイ |

## コマンド

| コマンド | 説明 |
|---|---|
| `!ping` | Pong! と返す |
| `!hello` | あいさつする |
