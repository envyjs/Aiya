@bot.slash_command(
    name="joinvoice",
    description="Join the voice channel you are currently on.",
    guild_ids=guild_ids,
)
async def join_vc(ctx: nextcord.Interaction):
    voice_client, joined = await _get_or_create_voice_client(ctx)
    if voice_client is None:
        await ctx.response.send_message(
            "Aiya cannot join a voice channel if you aren't in any!",
            ephemeral=True,
        )
    elif ctx.user.voice and voice_client.channel.id != ctx.user.voice.channel.id:
        old_channel_name = voice_client.channel.name
        await voice_client.disconnect()
        voice_client = await ctx.user.voice.channel.connect()
        new_channel_name = voice_client.channel.name
        guild_to_voice_client[ctx.guild.id] = (voice_client, datetime.utcnow())
        await ctx.response.send_message(
            f"Switched from #{old_channel_name} to #{new_channel_name}!"
        )
    else:
        await ctx.response.send_message("Connected to voice channel!")
        guild_to_voice_client[ctx.guild.id] = (voice_client, datetime.utcnow())
