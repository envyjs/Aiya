@bot.slash_command(name="leavevoice", description="Leave the voice chat it is currently on.", guild_ids=guild_ids)
async def leavevoice(ctx: nextcord.Interaction):
    if ctx.guild.id in guild_to_voice_client:
        voice_client, _ = guild_to_voice_client.pop(ctx.guild.id)
        await voice_client.disconnect()
        await ctx.response.send_message("Disconnected from voice channel")
    else:
        await ctx.response.send_message(
            "Aiya is not connected to a voice channel at this time. There is nothing to kick.", ephemeral=True
        )