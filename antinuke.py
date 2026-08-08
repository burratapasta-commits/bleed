# ═══════════════════════════ CATEGORY 2: ANTINUKE (18 commands) ═══════════════════════════

@bot.group(name="antinuke", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def antinuke_group(ctx):
    await ctx.send(embed=bleed_embed("Antinuke", "`admin`, `whitelist`, `ban`, `kick`, `role`, `channel`, `emoji`, `webhook`, `botadd`, `vanity`, `config`, `list`, `admins`, `permissions`, `enable`, `disable`, `reset`, `threshold`"))

@antinuke_group.command(name="admin")
async def antinuke_admin(ctx, user: discord.Member):
    """Toggle a user as an antinuke admin."""
    r = db.fetchone("SELECT admin FROM antinuke_whitelist WHERE guild_id=? AND user_id=?", (ctx.guild.id, user.id))
    na = 0 if (r and r[0]) else 1
    db.execute("INSERT OR REPLACE INTO antinuke_whitelist VALUES (?,?,?)", (ctx.guild.id, user.id, na))
    await ctx.send(embed=bleed_embed("Antinuke Admin", f"{user.mention} {'added as' if na else 'removed from'} admin."))

@antinuke_group.command(name="whitelist")
async def antinuke_whitelist(ctx, user: discord.Member):
    """Whitelist or unwhitelist a user from antinuke actions."""
    r = db.fetchone("SELECT * FROM antinuke_whitelist WHERE guild_id=? AND user_id=? AND admin=0", (ctx.guild.id, user.id))
    if r:
        db.execute("DELETE FROM antinuke_whitelist WHERE guild_id=? AND user_id=? AND admin=0", (ctx.guild.id, user.id))
        await ctx.send(embed=bleed_embed("Whitelist", f"{user.mention} removed from whitelist."))
    else:
        db.execute("INSERT OR IGNORE INTO antinuke_whitelist VALUES (?,?,0)", (ctx.guild.id, user.id))
        await ctx.send(embed=bleed_embed("Whitelist", f"{user.mention} whitelisted from antinuke."))

@antinuke_group.command(name="ban")
async def antinuke_ban(ctx, toggle: str = "on", threshold: int = None, *, punishment: str = None):
    """Configure mass ban prevention. --threshold N --do warn/jail/kick/ban/delete/stripstaff"""
    db.execute("INSERT OR IGNORE INTO antinuke (guild_id) VALUES (?)", (ctx.guild.id,))
    if toggle.lower() in ("on", "off"):
        db.execute("UPDATE antinuke SET enabled=? WHERE guild_id=?", (1 if toggle.lower() == "on" else 0, ctx.guild.id))
    if threshold:
        db.execute("UPDATE antinuke SET ban_threshold=? WHERE guild_id=?", (threshold, ctx.guild.id))
    r = db.fetchone("SELECT ban_threshold, enabled FROM antinuke WHERE guild_id=?", (ctx.guild.id,))
    status = "Enabled" if r and r[1] else "Disabled"
    await ctx.send(embed=bleed_embed("Ban Protection", f"Status: {status}\nThreshold: {r[0] if r else 3}/min\nPunishment: {punishment or 'ban'}"))

@antinuke_group.command(name="kick")
async def antinuke_kick(ctx, toggle: str = "on", threshold: int = None, *, punishment: str = None):
    """Configure mass kick prevention."""
    db.execute("INSERT OR IGNORE INTO antinuke (guild_id) VALUES (?)", (ctx.guild.id,))
    if threshold:
        db.execute("UPDATE antinuke SET kick_threshold=? WHERE guild_id=?", (threshold, ctx.guild.id))
    r = db.fetchone("SELECT kick_threshold FROM antinuke WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Kick Protection", f"Threshold: {r[0] if r else 3}/min\nPunishment: {punishment or 'ban'}"))

@antinuke_group.command(name="role")
async def antinuke_role(ctx, toggle: str = "on", threshold: int = None, *, punishment: str = None):
    """Configure mass role deletion prevention."""
    db.execute("INSERT OR IGNORE INTO antinuke (guild_id) VALUES (?)", (ctx.guild.id,))
    if threshold:
        db.execute("UPDATE antinuke SET role_threshold=? WHERE guild_id=?", (threshold, ctx.guild.id))
    r = db.fetchone("SELECT role_threshold FROM antinuke WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Role Protection", f"Threshold: {r[0] if r else 5}/min\nPunishment: {punishment or 'ban'}"))

@antinuke_group.command(name="channel")
async def antinuke_channel(ctx, toggle: str = "on"):
    """Toggle mass channel creation/deletion prevention."""
    en = 1 if toggle.lower() == "on" else 0
    db.execute("INSERT OR IGNORE INTO antinuke (guild_id) VALUES (?)", (ctx.guild.id,))
    db.execute("UPDATE antinuke SET channel_enabled=? WHERE guild_id=?", (en, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Channel Protection", f"{'Enabled' if en else 'Disabled'}"))

@antinuke_group.command(name="emoji")
async def antinuke_emoji(ctx, toggle: str = "on"):
    """Toggle mass emoji deletion prevention."""
    en = 1 if toggle.lower() == "on" else 0
    db.execute("INSERT OR IGNORE INTO antinuke (guild_id) VALUES (?)", (ctx.guild.id,))
    db.execute("UPDATE antinuke SET emoji_enabled=? WHERE guild_id=?", (en, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Emoji Protection", f"{'Enabled' if en else 'Disabled'}"))

@antinuke_group.command(name="webhook")
async def antinuke_webhook(ctx, toggle: str = "on"):
    """Toggle mass webhook creation prevention."""
    en = 1 if toggle.lower() == "on" else 0
    db.execute("INSERT OR IGNORE INTO antinuke (guild_id) VALUES (?)", (ctx.guild.id,))
    db.execute("UPDATE antinuke SET webhook_enabled=? WHERE guild_id=?", (en, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Webhook Protection", f"{'Enabled' if en else 'Disabled'}"))

@antinuke_group.command(name="botadd")
async def antinuke_botadd(ctx, toggle: str = "on"):
    """Toggle mass bot addition prevention."""
    en = 1 if toggle.lower() == "on" else 0
    db.execute("INSERT OR IGNORE INTO antinuke (guild_id) VALUES (?)", (ctx.guild.id,))
    db.execute("UPDATE antinuke SET bot_enabled=? WHERE guild_id=?", (en, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Bot Add Protection", f"{'Enabled' if en else 'Disabled'}"))

@antinuke_group.command(name="vanity")
async def antinuke_vanity(ctx, toggle: str = "on"):
    """Toggle vanity URL change prevention."""
    en = 1 if toggle.lower() == "on" else 0
    db.execute("INSERT OR IGNORE INTO antinuke (guild_id) VALUES (?)", (ctx.guild.id,))
    db.execute("UPDATE antinuke SET vanity_enabled=? WHERE guild_id=?", (en, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Vanity Protection", f"{'Enabled' if en else 'Disabled'}"))

@antinuke_group.command(name="config")
async def antinuke_config(ctx):
    """View current antinuke configuration."""
    r = db.fetchone("SELECT * FROM antinuke WHERE guild_id=?", (ctx.guild.id,))
    if not r:
        return await ctx.send(embed=bleed_embed("Antinuke", "Not configured. Use antinuke commands to set up."))
    e = discord.Embed(title="Antinuke Configuration", color=0x9B59B6)
    e.set_footer(text="bleed.bot • Antinuke")
    e.add_field(name="Status", value="Enabled" if r[1] else "Disabled", inline=True)
    e.add_field(name="Ban Threshold", value=f"{r[2]}/min", inline=True)
    e.add_field(name="Kick Threshold", value=f"{r[3]}/min", inline=True)
    e.add_field(name="Role Threshold", value=f"{r[4]}/min", inline=True)
    e.add_field(name="Channel", value="On" if r[5] else "Off", inline=True)
    e.add_field(name="Emoji", value="On" if r[6] else "Off", inline=True)
    e.add_field(name="Webhook", value="On" if r[7] else "Off", inline=True)
    e.add_field(name="Bot Add", value="On" if r[8] else "Off", inline=True)
    e.add_field(name="Vanity", value="On" if r[9] else "Off", inline=True)
    await ctx.send(embed=e)

@antinuke_group.command(name="list")
async def antinuke_list(ctx):
    """View all whitelisted users."""
    rows = db.fetchall("SELECT user_id FROM antinuke_whitelist WHERE guild_id=? AND admin=0", (ctx.guild.id,))
    wl = ", ".join([f"<@{r[0]}>" for r in rows]) if rows else "None"
    await ctx.send(embed=bleed_embed("Antinuke Whitelist", wl))

@antinuke_group.command(name="admins")
async def antinuke_admins(ctx):
    """View all antinuke admin users."""
    rows = db.fetchall("SELECT user_id FROM antinuke_whitelist WHERE guild_id=? AND admin=1", (ctx.guild.id,))
    adm = ", ".join([f"<@{r[0]}>" for r in rows]) if rows else "None"
    await ctx.send(embed=bleed_embed("Antinuke Admins", adm))

@antinuke_group.command(name="permissions")
async def antinuke_permissions(ctx, member: discord.Member = None):
    """Check a user's antinuke permissions."""
    m = member or ctx.author
    admin_row = db.fetchone("SELECT admin FROM antinuke_whitelist WHERE guild_id=? AND user_id=?", (ctx.guild.id, m.id))
    wl_row = db.fetchone("SELECT * FROM antinuke_whitelist WHERE guild_id=? AND user_id=? AND admin=0", (ctx.guild.id, m.id))
    is_admin = admin_row and admin_row[0] == 1
    is_whitelisted = wl_row is not None
    await ctx.send(embed=bleed_embed(f"Permissions: {m.name}", f"Antinuke Admin: {'Yes' if is_admin else 'No'}\nWhitelisted: {'Yes' if is_whitelisted else 'No'}"))

@antinuke_group.command(name="enable")
async def antinuke_enable(ctx):
    """Enable all antinuke modules."""
    db.execute("INSERT OR REPLACE INTO antinuke (guild_id,enabled,channel_enabled,emoji_enabled,webhook_enabled,bot_enabled,vanity_enabled) VALUES (?,1,1,1,1,1,1)", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Antinuke", "All modules enabled."))

@antinuke_group.command(name="disable")
async def antinuke_disable(ctx):
    """Disable all antinuke modules."""
    db.execute("UPDATE antinuke SET enabled=0,channel_enabled=0,emoji_enabled=0,webhook_enabled=0,bot_enabled=0,vanity_enabled=0 WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Antinuke", "All modules disabled."))

@antinuke_group.command(name="reset")
async def antinuke_reset(ctx):
    """Reset antinuke to default settings."""
    db.execute("DELETE FROM antinuke WHERE guild_id=?", (ctx.guild.id,))
    db.execute("DELETE FROM antinuke_whitelist WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Antinuke", "Reset to defaults. All whitelist entries cleared."))

@antinuke_group.command(name="threshold")
async def antinuke_threshold(ctx, module: str, value: int):
    """Quick-set threshold for a specific module. Usage: ,antinuke threshold ban 5"""
    module_map = {"ban": "ban_threshold", "kick": "kick_threshold", "role": "role_threshold"}
    if module not in module_map:
        return await ctx.send(embed=error_embed("Valid modules: `ban`, `kick`, `role`"))
    db.execute("INSERT OR IGNORE INTO antinuke (guild_id) VALUES (?)", (ctx.guild.id,))
    db.execute(f"UPDATE antinuke SET {module_map[module]}=? WHERE guild_id=?", (value, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Threshold Updated", f"{module.title()}: {value}/min"))
