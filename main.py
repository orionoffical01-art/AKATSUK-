import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from datetime import datetime
import sqlite3

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Veritabanı
def init_db():
    conn = sqlite3.connect('akatsuki.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS servers (
        guild_id INTEGER PRIMARY KEY,
        prefix TEXT,
        log_channel INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        user_id INTEGER,
        channel_id INTEGER,
        reason TEXT,
        created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        guild_id INTEGER,
        user_id INTEGER,
        messages INTEGER,
        warnings INTEGER
    )''')
    conn.commit()
    conn.close()

@bot.event
async def on_ready():
    print(f'{bot.user} aktif!')
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)} komut senkronize edildi')
    except:
        pass
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Akatsuki 🔴⚫"
        )
    )

@bot.event
async def on_member_join(member):
    conn = sqlite3.connect('akatsuki.db')
    c = conn.cursor()
    c.execute('SELECT log_channel FROM servers WHERE guild_id = ?', (member.guild.id,))
    result = c.fetchone()
    
    if result:
        channel = bot.get_channel(result[0])
        if channel:
            embed = discord.Embed(
                title="✅ Yeni Üye",
                description=f"{member.mention} katıldı",
                color=discord.Color.green()
            )
            await channel.send(embed=embed)
    
    try:
        role = discord.utils.get(member.guild.roles, name="Member")
        if role:
            await member.add_roles(role)
    except:
        pass
    
    conn.close()

@bot.tree.command(name="ping", description="Ping'i göster")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! {bot.latency * 1000:.2f}ms"
    )

@bot.tree.command(name="setup", description="Bot'u ayarla")
async def setup(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admin gerekli!", ephemeral=True)
        return
    
    try:
        await interaction.guild.create_role(name="Member", color=discord.Color.red())
        await interaction.guild.create_role(name="Moderator", color=discord.Color.orange())
    except:
        pass
    
    try:
        log_channel = await interaction.guild.create_text_channel("📋bot-logs")
        
        conn = sqlite3.connect('akatsuki.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO servers (guild_id, log_channel) VALUES (?, ?)',
                  (interaction.guild.id, log_channel.id))
        conn.commit()
        conn.close()
    except:
        pass
    
    await interaction.response.send_message("✅ Kurulum tamamlandı!")

async def main():
    init_db()
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Token bulunamadı!")
        return
    await bot.start(token)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
