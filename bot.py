import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from datetime import datetime, timedelta

# Load bot token from environment variables
TOKEN = os.environ.get('TOKEN')

# Channel & Role IDs (Update these with actual IDs)
DUTY_LOG_CHANNEL_ID = 1347456904795787352
BOT_LOG_CHANNEL_ID = 1347456904795787352  # Update with your bot log channel ID

# Set up bot with all intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="()e", intents=intents)

# Guild ID for syncing commands
GUILD_ID = 1347456902065553470

# Dictionary to track duty status and weekly reports
active_duty = {}
weekly_duty_hours = {}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    try:
        bot.tree.copy_global_to(guild=discord.Object(id=GUILD_ID))  # Copy global commands to the guild
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))  # Sync commands
        print(f"✅ Synced {len(synced)} commands: {[cmd.name for cmd in bot.tree.get_commands(guild=discord.Object(id=GUILD_ID))]}")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

    # Start weekly report task
    weekly_report.start()


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

        # Update weekly report
        if user.id in weekly_duty_hours:
            weekly_duty_hours[user.id] += elapsed_time.total_seconds()
        else:
            weekly_duty_hours[user.id] = elapsed_time.total_seconds()

        embed = discord.Embed(title="🔴 Clocked Out", color=discord.Color.red())
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.add_field(name="👮 Officer", value=user.mention, inline=True)
        embed.add_field(name="🕒 Clock In Time", value=clock_in_time.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="⏳ Total Time on Duty", value=elapsed_time_str, inline=True)
        embed.set_footer(text="Bayview Roleplay Duty System")

        await channel.send(embed=embed)

        # DM user
        dm_embed = discord.Embed(title="📌 Duty Status Update", color=discord.Color.orange())
        dm_embed.add_field(name="🟥 You are now OFF duty!", value="Your duty session has been logged.", inline=False)
        dm_embed.add_field(name="⏳ Time Spent on Duty", value=elapsed_time_str, inline=True)
        await user.send(embed=dm_embed)

        await interaction.response.send_message("✅ You are now **off duty**.", ephemeral=True)

    else:
        # Clocking in
        active_duty[user.id] = datetime.now()
        clock_in_time = active_duty[user.id]

        embed = discord.Embed(title="🟢 Clocked In", color=discord.Color.green())
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.add_field(name="👮 Officer", value=user.mention, inline=True)
        embed.add_field(name="🕒 Clock In Time", value=clock_in_time.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_footer(text="Bayview Roleplay Duty System")

        await channel.send(embed=embed)

        # DM user
        dm_embed = discord.Embed(title="📌 Duty Status Update", color=discord.Color.green())
        dm_embed.add_field(name="🟩 You are now ON duty!", value="Your duty time has started.", inline=False)
        dm_embed.add_field(name="📍 Remember", value="Use `/duty` to clock out when you're done.", inline=False)
        await user.send(embed=dm_embed)

        await interaction.response.send_message("✅ You are now **on duty**.", ephemeral=True)


# 🗓️ Weekly Duty Report
@tasks.loop(hours=168)  # Runs every 7 days
async def weekly_report():
    channel = bot.get_channel(DUTY_LOG_CHANNEL_ID)
    if not channel:
        print("⚠️ Duty log channel not found.")
        return

    if not weekly_duty_hours:
        print("ℹ️ No duty hours recorded this week.")
        return

    embed = discord.Embed(title="📆 Weekly Duty Report", color=discord.Color.blue())
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)

    for user_id, seconds in weekly_duty_hours.items():
        user = await bot.fetch_user(user_id)
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        embed.add_field(name=f"👮 {user.name}", value=f"⏳ {int(hours)}h {int(minutes)}m", inline=False)

        # DM individual report
        dm_embed = discord.Embed(title="📆 Your Weekly Duty Report", color=discord.Color.blue())
        dm_embed.add_field(name="Total Time on Duty", value=f"⏳ {int(hours)}h {int(minutes)}m", inline=True)
        await user.send(embed=dm_embed)

    embed.set_footer(text="Bayview Roleplay Duty System")
    await channel.send(embed=embed)

    # Reset weekly hours
    weekly_duty_hours.clear()


# Run the bot
bot.run(TOKEN)
