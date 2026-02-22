import discord
from discord.ext import commands
import random
from datetime import datetime
import os
import psutil
import json
from flask import Flask
from threading import Thread

# --- RENDER KEEP-ALIVE ---
app = Flask('')
@app.route('/')
def home():
    return "Aries Bot: Titan System Online 🛡️"

def run_flask():
    try: app.run(host='0.0.0.0', port=8080)
    except Exception as e: print(f"Flask Error: {e}")

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN") 
APP_ID = os.getenv("APPLICATION_ID")
TARGET_SERVER_ID = 770004215678369883
TARGET_CHANNEL_ID = 1426247870495068343
LEADER_ROLE_ID = 1412430417578954983 
DATA_FILE = "leader_msgs.json"

# --- DATA MANAGEMENT ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: return json.load(f)
    return {
        "online_msg": "🛡️ **Order is restored. Leader {user_name} is watching.**",
        "offline_msg": "Leader **{user_name}** is offline — <@&1018171797126004827> stay active, **ARIES Citizen** take charge, track the leaderboard, and hold our clan position."
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f)

# --- UI COMPONENTS ---
class SetLeaderView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

    @discord.ui.select(
        placeholder="Select Mode (Online ya Offline)",
        options=[
            discord.SelectOption(label="Online Message", value="online_msg"),
            discord.SelectOption(label="Offline Message", value="offline_msg")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.bot.waiting_for_input[interaction.user.id] = select.values[0]
        await interaction.response.send_message(f"✅ Mode select hua: **{select.values[0]}**. Ab apna naya message bhejein (placeholders use kar sakte hain: {{user_name}}).", ephemeral=True)

# --- BOT CLASS ---
class AriesBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents, application_id=APP_ID)
        self.active_sessions = {}
        self.start_time = datetime.utcnow()
        self.waiting_for_input = {}
        self.leader_msgs = load_data()

bot = AriesBot()

# --- COMMANDS ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setleader(ctx):
    view = SetLeaderView(bot)
    await ctx.send("⚙️ Leader ke messages configure karne ke liye select karein:", view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def status(ctx):
    latency = round(bot.latency * 1000)
    memory = psutil.Process(os.getpid()).memory_info().rss / 1024**2
    embed = discord.Embed(title="⚙️ Aries Self-Diagnostic", color=0x3498db)
    embed.add_field(name="📡 Latency", value=f"`{latency}ms`", inline=True)
    embed.add_field(name="💾 RAM", value=f"`{memory:.1f}MB`", inline=True)
    embed.add_field(name="🛡️ Protection", value="`MAX (Auto-Heal)`", inline=False)
    await ctx.send(embed=embed)

# --- MAIN ENGINE ---
@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    # 1. Custom Message Input Logic
    if message.author.id in bot.waiting_for_input:
        mode = bot.waiting_for_input.pop(message.author.id)
        bot.leader_msgs[mode] = message.content
        save_data(bot.leader_msgs)
        await message.channel.send(f"✅ Success! Updated `{mode}`.")
        return

    # 2. Existing Attendance Logic
    if message.guild and message.guild.id == TARGET_SERVER_ID and message.channel.id == TARGET_CHANNEL_ID:
        content = message.content.lower().strip()
        user = message.author
        now = datetime.utcnow()
        is_leader = any(role.id == LEADER_ROLE_ID for role in user.roles)

        if content == "online":
            await message.delete()
            if user.id not in bot.active_sessions:
                bot.active_sessions[user.id] = now
                msg = bot.leader_msgs["online_msg"].replace("{user_name}", user.display_name) if is_leader else f"✅ **{user.display_name}** has started their session."
                embed = discord.Embed(title="Status: ONLINE", description=msg, color=0xf1c40f if is_leader else 0x2ecc71)
                await message.channel.send(embed=embed)

        elif content == "offline":
            await message.delete()
            if user.id in bot.active_sessions:
                start_time = bot.active_sessions[user.id]
                duration = now - start_time
                msg = bot.leader_msgs["offline_msg"].replace("{user_name}", user.display_name) if is_leader else f"🔴 **{user.display_name}** session ended."
                embed = discord.Embed(title="Status: OFFLINE", description=msg, color=0x2f3136 if is_leader else 0xe74c3c)
                await message.channel.send(embed=embed)
                del bot.active_sessions[user.id]

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} Deployment Successful!')

if __name__ == "__main__":
    keep_alive()
    if TOKEN: bot.run(TOKEN)
