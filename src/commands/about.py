@bot.slash_command(name="about", description="Shows about this bot and it's credits.")
async def about(interaction: nextcord.Interaction):
    try:
        await interaction.user.send("# About Envy Aiya"),await interaction.user.send("Envy Aiya is a work in progress spiritual successor to Restarter v3."),await interaction.user.send("Aiya support server: https://discord.gg/fHMsFvefab"),await interaction.user.send("# Aiya credits"),await interaction.user.send("Ayix - Lead developer"),await interaction.user.send("Steeldev and the Nexus project - for the original codebase"),await interaction.user.send("Nexus support server: https://discord.gg/d2fvJ3TmhV")
        await interaction.response.send_message("Aiya has successfully sent the DM!", ephemeral=True)
    except nextcord.Forbidden:
        await interaction.response.send_message("Aiya cannot send the DM.", ephemeral=True)