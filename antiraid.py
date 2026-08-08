# ═══════════════════════════ CATEGORY 3: JOIN GATE / ANTIRAID (12 commands) ═══════════════════════════

@bot.group(name="antiraid", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def antiraid_group(ctx):
    """Join gate and anti-raid configuration."""
    await ctx.send(embed=bleed_embed("Join Gate / Antiraid", "`massjoin`, `avatar`, `age`, `whitelist`, `whitelist add`, `whitelist remove`, `whitelist clear`, `whitelist view`, `config`, `state`, `enable`, `disable`"))

@antiraid_group.command(name="massjoin")
async def antiraid_massjoin(ctx, toggle: str = "on", threshold: int = 10, *, punishment: str = "kick"):
    """
    Configure mass join protection.
    Flags: --threshold N, --do ban/kick, --lock, --punish
    """
    db.execute("INSERT OR IGNORE INTO joingate (guild_id) VALUES (?)", (ctx.guild.id,))
    en = 1 if toggle.lower() == "on" else 0
    db.execute(
        "UPDATE joingate SET enabled=?, massjoin_threshold=?, massjoin_punishment=? WHERE guild_id=?",
        (en, threshold, punishment, ctx.guild.id)
    )
    await ctx.send(embed=bleed_embed(
        "Mass Join Protection",
        f"Status: {'Enabled' if en else 'Disabled'}\nThreshold: {threshold} joins/min\nPunishment: {punishment}"
    ))

@antiraid_group.command(name="avatar")
async def antiraid_avatar(ctx, toggle: str = "on"):
    """Toggle blocking members without profile avatars."""
    db.execute("INSERT OR IGNORE INTO joingate (guild_id) VALUES (?)", (ctx.guild.id,))
    en = 1 if toggle.lower() == "on" else 0
    db.execute("UPDATE joingate SET avatar_enabled=? WHERE guild_id=?", (en, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Avatar Protection", f"{'Enabled' if en else 'Disabled'}"))

@antiraid_group.command(name="age")
async def antiraid_age(ctx, toggle: str = "on", min_days: int = 7):
    """Toggle blocking accounts newer than X days."""
    db.execute("INSERT OR IGNORE INTO joingate (guild_id) VALUES (?)", (ctx.guild.id,))
    en = 1 if toggle.lower() == "on" else 0
    db.execute("UPDATE joingate SET age_enabled=?, age_min=? WHERE guild_id=?", (en, min_days, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Age Protection", f"Status: {'Enabled' if en else 'Disabled'}\nMinimum age: {min_days} days"))

@antiraid_group.command(name="whitelist")
async def antiraid_whitelist(ctx, user: discord.Member = None):
    """View whitelisted users or toggle a user's whitelist status."""
    if user:
        r = db.fetchone("SELECT * FROM joingate_whitelist WHERE guild_id=? AND user_id=?", (ctx.guild.id, user.id))
        if r:
            db.execute("DELETE FROM joingate_whitelist WHERE guild_id=? AND user_id=?", (ctx.guild.id, user.id))
            await ctx.send(embed=bleed_embed("Join Gate Whitelist", f"{user.mention} removed from whitelist."))
        else:
            db.execute("INSERT INTO joingate_whitelist VALUES (?,?)", (ctx.guild.id, user.id))
            await ctx.send(embed=bleed_embed("Join Gate Whitelist", f"{user.mention} whitelisted."))
    else:
        rows = db.fetchall("SELECT user_id FROM joingate_whitelist WHERE guild_id=?", (ctx.guild.id,))
        users = ", ".join([f"<@{r[0]}>" for r in rows]) if rows else "None"
        await ctx.send(embed=bleed_embed("Join Gate Whitelist", users))

@antiraid_group.command(name="config")
async def antiraid_config(ctx):
    """View current join gate configuration."""
    r = db.fetchone("SELECT * FROM joingate WHERE guild_id=?", (ctx.guild.id,))
    if not r:
        return await ctx.send(embed=bleed_embed("Join Gate", "Not configured. Use `,antiraid massjoin on` to enable."))
    embed = discord.Embed(title="Join Gate Configuration", color=0x9B59B6)
    embed.set_footer(text="bleed.bot • Join Gate")
    embed.add_field(name="Status", value="Enabled" if r[1] else "Disabled", inline=True)
    embed.add_field(name="Mass Join Threshold", value=f"{r[2]}/min", inline=True)
    embed.add_field(name="Punishment", value=r[3], inline=True)
    embed.add_field(name="Avatar Check", value="On" if r[4] else "Off", inline=True)
    embed.add_field(name="Age Check", value=f"On ({r[6]}d)" if r[5] else "Off", inline=True)
    await ctx.send(embed=embed)

@antiraid_group.command(name="state")
async def antiraid_state(ctx):
    """Check if join gate is currently active."""
    r = db.fetchone("SELECT enabled FROM joingate WHERE guild_id=?", (ctx.guild.id,))
    status = "Enabled" if r and r[0] else "Disabled"
    await ctx.send(embed=bleed_embed("Join Gate State", status))

@antiraid_group.command(name="enable")
async def antiraid_enable(ctx):
    """Enable join gate protection."""
    db.execute("INSERT OR IGNORE INTO joingate (guild_id,enabled) VALUES (?,1)", (ctx.guild.id,))
    db.execute("UPDATE joingate SET enabled=1 WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Join Gate", "Enabled."))

@antiraid_group.command(name="disable")
async def antiraid_disable(ctx):
    """Disable join gate protection."""
    db.execute("UPDATE joingate SET enabled=0 WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Join Gate", "Disabled."))

@antiraid_group.command(name="lockdown")
async def antiraid_lockdown(ctx):
    """Emergency lockdown — lock all channels and enable join gate."""
    # Enable join gate
    db.execute("INSERT OR IGNORE INTO joingate (guild_id,enabled,massjoin_threshold,massjoin_punishment) VALUES (?,1,5,'ban')", (ctx.guild.id,))
    db.execute("UPDATE joingate SET enabled=1, massjoin_threshold=5, massjoin_punishment='ban' WHERE guild_id=?", (ctx.guild.id,))
    # Lock all channels
    locked = 0
    for ch in ctx.guild.text_channels:
        try:
            await ch.set_permissions(ctx.guild.default_role, send_messages=False)
            locked += 1
        except:
            pass
    await ctx.send(embed=bleed_embed("Emergency Lockdown", f"Join gate enabled (5 joins/min → ban)\n{locked} channels locked."))

@antiraid_group.command(name="unlock")
async def antiraid_unlock(ctx):
    """Release emergency lockdown."""
    db.execute("UPDATE joingate SET enabled=0 WHERE guild_id=?", (ctx.guild.id,))
    unlocked = 0
    for ch in ctx.guild.text_channels:
        try:
            await ch.set_permissions(ctx.guild.default_role, send_messages=True)
            unlocked += 1
        except:
            pass
    await ctx.send(embed=bleed_embed("Lockdown Released", f"Join gate disabled.\n{unlocked} channels unlocked."))
