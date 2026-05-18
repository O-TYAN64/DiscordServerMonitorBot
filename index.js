const { Client, GatewayIntentBits, Events } = require('discord.js');

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

// Bot 起動時
client.once(Events.ClientReady, (c) => {
  console.log(`✅ Logged in as ${c.user.tag}`);
});

// メッセージ受信時
client.on(Events.MessageCreate, async (message) => {
  // Bot 自身のメッセージは無視
  if (message.author.bot) return;

  // コマンド例: !ping
  if (message.content === '!ping') {
    await message.reply('🏓 Pong!');
  }

  // コマンド例: !hello
  if (message.content === '!hello') {
    await message.reply(`👋 こんにちは、${message.author.displayName}さん！`);
  }
});

// エラーハンドリング
client.on(Events.Error, (error) => {
  console.error('Discord client error:', error);
});

client.login(process.env.DISCORD_TOKEN);
