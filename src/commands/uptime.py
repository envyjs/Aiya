@bot.slash_command(description="Reports the uptime of Aiya")
async def uptime(ctx):
    embed = nextcord.Embed(
            title="⏰ Uptime",
            color=nextcord.Color.red()
    )
    embed.insert_field_at(1, name = f"""Started""", value= startDay, inline=False)
    embed.insert_field_at(1, name = f"""Alive (HH:MM:SS)""", value=datetime.now() - startTime, inline=False)
    await ctx.send(embed=embed)