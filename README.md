# 🖥️ Discord Server Monitor Bot v2

A Discord bot that checks server status via slash commands.  
When a command is received, **GitHub Actions** runs the check and posts the result to Discord as an Embed.

---

## Supported Server Types

| Type | What is checked |
| --- | --- |
| `minecraft` | SLP protocol (version, MOTD, player count) |
| `ark` | Steam A2S (map, player count) |
| `valheim` | Steam A2S |
| `rust` | Steam A2S |
| `cs2` / `csgo` | Steam A2S |
| `palworld` | Steam A2S |
| `7dtd` | Steam A2S |
| `terraria` | TCP ping + REST API (tModLoader) |
| `vrchat` | VRChat official API (world, occupancy) |
| `steam_query` | Steam A2S (generic) |
| `web` | HTTP/HTTPS status code & latency |
| `api` | Custom REST endpoint |
| `steam_server_list` | Server info via Steam Web API |
| `game_server_api` | Generic API via api.gameserverapi.com |
| `aws` | AWS Health Dashboard |
| `cloudflare` | Cloudflare Status + Zone API |

---

## Setup

### 1. Create a Discord Bot

1. Create an application at the [Discord Developer Portal](https://discord.com/developers/applications)
2. Go to the **Bot** tab → copy the token
3. In **OAuth2 → URL Generator**, select `bot` + `applications.commands`
4. Grant permissions: `Send Messages`, `Embed Links`, then invite the bot to your server

### 2. Create a Discord Webhook

In the channel where you want results posted, go to **Settings → Integrations → Webhooks**, create a webhook, and copy its URL.

### 3. Configure GitHub Secrets

| Secret Name | Required | Description |
| --- | --- | --- |
| `DISCORD_TOKEN` | ✅ | Discord Bot token |
| `DISCORD_WEBHOOK` | ✅ | Discord Webhook URL |
| `GH_PAT` | ✅ | GitHub PAT (`workflow` scope) |
| `STEAM_API_KEY` | ☑️ | Steam Web API key (for `steam_server_list` type) |
| `GAME_SERVER_API_KEY` | ☑️ | Game Server API key |
| `CF_API_KEY` | ☑️ | Cloudflare API key (for zone check) |
| `CF_ZONE_ID` | ☑️ | Cloudflare Zone ID |

---

## Slash Commands

| Command | Description |
| --- | --- |
| `/status` | Check the status of all servers |
| `/status name:<id>` | Check the status of a specific server |
| `/add_server name:<id> type:<type> host:<host>` | Add a server |
| `/remove_server name:<id>` | Remove a server |
| `/list_servers` | List all registered servers |
| `/server_types` | Display a list of supported server types |

### Add Server Examples

```
# Minecraft
/add_server name:mc1 type:minecraft host:mc.example.com port:25565 label:My MC Server

# ARK
/add_server name:ark1 type:ark host:192.168.1.100 port:7777

# Fetch server via Steam Web API
/add_server name:rust1 type:steam_server_list host:1.2.3.4 port:28015

# Game Server API
/add_server name:rust2 type:game_server_api host:1.2.3.4 port:28015 extra:{"game":"rust"}

# Custom REST API (online determined by expect_key/expect_value)
/add_server name:myapi type:api host:https://myserver.com endpoint:/api/health extra:{"expect_key":"status","expect_value":"ok"}

# AWS Tokyo region
/add_server name:aws_tokyo type:aws host:ap-northeast-1 extra:{"services":"ec2,rds,s3"}

# Cloudflare + Zone check
/add_server name:cf type:cloudflare host:global extra:{"cf_zone_id":"your_zone_id"}

# Terraria (with REST API enabled)
/add_server name:terra type:terraria host:1.2.3.4 port:7777 extra:{"rest_port":7878}
```

---

## File Structure

```
discord-server-monitor/
├── .github/workflows/
│   ├── check_status.yml   # Status check (workflow_dispatch)
│   └── run_bot.yml        # Discord Bot startup
├── src/
│   ├── bot.py             # Discord Bot
│   ├── checkers.py        # Checkers for all server types
│   ├── embeds.py          # Discord Embed generation
│   └── check_status.py    # Actions entry point
├── config/
│   └── servers.json       # Monitored server configuration
└── requirements.txt
```

---

## How It Works

```
Discord User (/status)
       │
       ▼
bot.py  (triggers GitHub Actions workflow_dispatch)
       │
       ▼
check_status.yml  (GitHub Actions)
       │
       ▼
checkers.py  (runs checks per server type)
  ├─ Minecraft SLP
  ├─ Steam A2S (ARK / Valheim / Rust / CS2 / Palworld / 7DTD)
  ├─ VRChat API
  ├─ Steam Web API
  ├─ Game Server API
  ├─ AWS Health API
  ├─ Cloudflare Status API
  └─ HTTP / REST check
       │
       ▼
embeds.py  (generates Discord Embed)
       │
       ▼
Discord Webhook → posts result to channel
```
