import nextcord
from nextcord.ext import commands, tasks
from nextcord import ChannelType, Interaction, SlashOption
from nextcord.abc import GuildChannel
import sqlite3
from datetime import datetime, timedelta, date
import os
import asyncio
import re
from urllib.parse import urlparse
from flask import Flask, request
import threading
import arrow
from io import BytesIO
from time import sleep

startDay = arrow.now().format('YYYY-MM-DD')
startTime = datetime.now()
intents = nextcord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)
DEV_GUILD_ID = 1227835833386663947
guild_ids = [DEV_GUILD_ID]
guild_to_voice_client = dict()


statuses = ["Beta!", "Ear Dentist approved!", "Or is it?", "PLAP PLAP PLAP PLAP", "Fun for the whole family!"]

async def _get_or_create_voice_client(ctx: nextcord.Interaction):
    joined = False
    if ctx.guild.id in guild_to_voice_client:
        voice_client, _ = guild_to_voice_client[ctx.guild.id]
    else:
        voice_channel = _context_to_voice_channel(ctx)
        if voice_channel is None:
            voice_client = None
        else:
            voice_client = await voice_channel.connect()
            joined = True
    return (voice_client, joined)

def _context_to_voice_channel(ctx):
    return ctx.user.voice.channel if ctx.user.voice else None

async def terminate_stale_voice_connections():
    while True:
        await asyncio.sleep(5)
        for k in list(guild_to_voice_client.keys()):
            v = guild_to_voice_client[k]
            voice_client, last_used = v
            if datetime.utcnow() - last_used > timedelta(minutes=10):
                await voice_client.disconnect()
                guild_to_voice_client.pop(k)

async def update_status():
    for status in statuses:
        await bot.change_presence(activity=nextcord.Game(name=status))
        await asyncio.sleep(60)

conn = sqlite3.connect('nexus.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS channel_settings
             (server_id INTEGER, channel_id INTEGER, PRIMARY KEY (server_id, channel_id))''')
conn.commit()

async def reload_roles():
    global admin_ids, owner_ids, admin_emoji, owner_emoji
    while True:
        with open("admins.txt", "r", encoding="utf-8") as file:
            admin_ids = [int(line.strip()) for line in file]

        with open("settings.txt", "r", encoding="utf-8") as file:
            settings = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in file}
            admin_emoji = settings.get('admin_emoji', '🛡️')
            owner_emoji = settings.get('owner_emoji', '👑')

        with open("owners.txt", "r", encoding="utf-8") as file:
            owner_ids = [int(line.strip()) for line in file]
        
        await asyncio.sleep(5)

bot.loop.create_task(reload_roles())

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    update_status_loop.start()
    
update_status_loop = tasks.loop(seconds=5)(update_status)

def format_timestamp(timestamp):
    now = datetime.utcnow()
    message_time = datetime.utcfromtimestamp(timestamp)
    if message_time.date() == now.date():
        return f"Today at {message_time.strftime('%I:%M %p')}"
    elif message_time.date() == now.date() - timedelta(days=1):
        return f"Yesterday at {message_time.strftime('%I:%M %p')}"
    else:
        return message_time.strftime('%Y-%m-%d at %I:%M %p')

@bot.event
async def on_message(message):
    if message.author.bot or message.content.startswith('/'):
        return
    with open("banned_users.txt", "r") as banned_file:
        banned_users = banned_file.readlines()
        banned_users = [user.strip() for user in banned_users]

    if str(message.author.id) in banned_users:
        embed = nextcord.Embed(
            title="You are banned from cross-server chatting.",
            description="You were banned for breaking the rules of the Envy Community Guidelines.",
            color=nextcord.Color.red()
        )
        try:
            await message.author.send(embed=embed)
        except nextcord.Forbidden:
            pass
        await message.delete()
        return

    c.execute("SELECT channel_id FROM channel_settings WHERE server_id = ?", (message.guild.id,))
    set_channel_id = c.fetchone()
    if set_channel_id and message.channel.id == set_channel_id[0]:
        links = re.findall(r'https?://\S+', message.content)
        if links:
            unblocked_domains = []
            with open("unblocked_links.txt", "r", encoding="utf-8") as file:
                for line in file:
                    unblocked_domains.append(urlparse(line.strip()).netloc)
            
            allow_message = False
            for link in links:
                domain = urlparse(link).netloc
                if domain in unblocked_domains:
                    allow_message = True
                    break
            
            if not allow_message:
                embed = nextcord.Embed(
                    title="Alert!",
                    description="You cannot send blacklisted links on Nexus.",
                    color=nextcord.Color.red()
                )
                try:
                    await message.author.send(embed=embed)
                except nextcord.Forbidden:
                    pass
                await message.delete()
                return

        await asyncio.gather(
            send_embed(message),
            delete_message(message)
        )

async def send_embed(message):
    server = bot.get_guild(message.guild.id)
    if server:
        if message.guild.id == 1227835833386663947:
            embed_color = nextcord.Color.green()
        else:
            embed_color = nextcord.Color.blue()
            
        embed = nextcord.Embed(
            description=f"{message.content}",
            color=embed_color
        )
        icon_url = message.author.avatar.url if message.author.avatar else None
        if icon_url:
            embed.set_author(name=f"{message.author.display_name} {admin_emoji if message.author.id in admin_ids else ''} {owner_emoji if message.author.id in owner_ids else ''}", icon_url=icon_url)
        else:
            embed.set_author(name=f"{message.author.display_name} | {message.author.id} | {admin_emoji if message.author.id in admin_ids else ''} {owner_emoji if message.author.id in owner_ids else ''}")

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        
        if message.author.id in admin_ids or message.author.id in owner_ids:
            embed.color = nextcord.Color.red()
        
        icon_url_guild = message.guild.icon.url if message.guild.icon else None
        if icon_url_guild:
            embed.set_footer(text=f"{server.name} - {format_timestamp(message.created_at.timestamp())}", icon_url=icon_url_guild)
        else:
            embed.set_footer(text=f"{server.name} - Envy Nexus - {format_timestamp(message.created_at.timestamp())}")
            
        if message.reference and message.reference.message_id:
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            if referenced_message and referenced_message.author.bot:
                referenced_description = referenced_message.embeds[0].description
                original_sender = referenced_message.embeds[0].author.name.split(' | ')[0]
                embed.insert_field_at(0, name="Replying to:", value=referenced_description, inline=False)
                embed.description = message.content
        
        c.execute("SELECT channel_id FROM channel_settings")
        results = c.fetchall()
        tasks = []
        for result in results:
            channel_id = result[0]
            channel = bot.get_channel(channel_id)
            if channel:
                tasks.append(send_message(channel, embed))

        await asyncio.gather(*tasks)

async def send_message(channel, embed):
    try:
        await channel.send(embed=embed)
    except nextcord.Forbidden:
        pass

async def delete_message(message):
    try:
        await message.delete()
    except nextcord.Forbidden:
        pass

def load_commands(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.py'):
            with open(os.path.join(directory, filename), 'r', encoding="utf-8") as file:
                exec(file.read())

load_commands("src/commands")

bot.run('token goes here')
