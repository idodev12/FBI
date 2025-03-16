import discord
from discord.ext import commands
from discord import app_commands
import os
from keep_alive import keep_alive
from datetime import datetime

# Load bot token from environment variables
TOKEN = os.environ.get('TOKEN')

# Channel & Role IDs (Update these with actual IDs)
DUTY_LOG_CHANNEL_ID = 1347456904795787352


# Set up bot with all intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="()e", intents=intents)

# Guild ID for syncing commands
GUILD_ID = 1347456902065553470

# Dictionary to track active duty users
active_duty = {}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    try:
        bot.tree.copy_global_to(guild=discord.Object(id=GUILD_ID))  # Copy global commands to the guild
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))  # Sync commands
        print(f"✅ Synced {len(synced)} commands: {[cmd.name for cmd in bot.tree.get_commands(guild=discord.Object(id=GUILD_ID))]}")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")
async def log_bot_activity(interaction: discord.Interaction, command_name: str):
    """Logs bot activity to the bot log channel."""
    bot_log_channel = bot.get_channel(BOT_LOG_CHANNEL_ID)
    if not bot_log_channel:
        print("⚠️ Bot log channel not found.")
        return
    
    embed = discord.Embed(title="📌 Bot Activity Log", color=discord.Color.dark_gray())
    embed.add_field(name="User", value=interaction.user.mention, inline=True)
    embed.add_field(name="Command", value=f"/{command_name}", inline=True)
    embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
    embed.set_footer(text=f"User ID: {interaction.user.id}")

    await bot_log_channel.send(embed=embed)

async def send_report(interaction, channel_id, embed):
    """Universal function to log reports."""
    channel = bot.get_channel(channel_id)
    if not channel:
        await interaction.followup.send("⚠️ Error: Log channel not found.", ephemeral=True)
        return
    
    await channel.send(embed=embed)
    await interaction.followup.send("✅ Report logged.", ephemeral=True)

# 🟢 Duty Command
@bot.tree.command(name="duty", description="Toggle duty status.")
async def duty(interaction: discord.Interaction):
    user = interaction.user
    channel = bot.get_channel(DUTY_LOG_CHANNEL_ID)

    if user.id in active_duty:
        # Clocking out
        clock_in_time = active_duty.pop(user.id)
        elapsed_time = datetime.now() - clock_in_time
        elapsed_time_str = str(elapsed_time).split(".")[0]  # Format as HH:MM:SS

        embed = discord.Embed(title="🔴 Clocked Out", color=discord.Color.red())
        embed.add_field(name="Officer", value=user.mention, inline=True)
        embed.add_field(name="Clock In Time", value=clock_in_time.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Total Time on Duty", value=elapsed_time_str, inline=True)

        await channel.send(embed=embed)
        await interaction.response.send_message("✅ You are now **off duty**.", ephemeral=True)
    else:
        # Clocking in
        active_duty[user.id] = datetime.now()
        clock_in_time = active_duty[user.id]

        embed = discord.Embed(title="🟢 Clocked In", color=discord.Color.green())
        embed.add_field(name="Officer", value=user.mention, inline=True)
        embed.add_field(name="Clock In Time", value=clock_in_time.strftime("%Y-%m-%d %H:%M:%S"), inline=True)

        await channel.send(embed=embed)
        await interaction.response.send_message("✅ You are now **on duty**.", ephemeral=True)


# Keep the bot alive (only applicable if using a web hosting service like Replit)
keep_alive()

# Run the bot
bot.run(TOKEN)
