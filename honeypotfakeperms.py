# ═══════════════════════════ CATEGORY 4: HONEYPOT (6 commands) ═══════════════════════════

@bot.group(name="honeypot", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def honeypot_group(ctx):
    """Honeypot channel management — catch unauthorized users."""
    await ctx.send(embed=bleed_embed("Honeypot", "`add`, `remove`, `list`, `enable`, `disable`, `config`"))

@honeypot_group.command(name="add")
async def honeypot_add(ctx, channel: discord.TextChannel, punishment: str = "ban"):
    """
    Add a honeypot channel.
    Punishments: ban, softban, jail
    """
    if punishment not in ("ban", "softban", "jail"):
        return await ctx.send(embed=error_embed("Punishment must be: `ban`, `softban`, or `jail`."))
    db.execute("INSERT OR REPLACE INTO honeypot VALUES (?,?,?)", (ctx.guild.id, channel.id, punishment))
    try:
        await channel.set_permissions(ctx.guild.default_role, view_channel=False)
    except (discord.Forbidden, discord.HTTPException):
        pass
    await ctx.send(embed=bleed_embed("Honeypot Added", f"{channel.mention} — Punishment: **{punishment}**\nAnyone who types in this channel will be punished."))

@honeypot_group.command(name="remove")
async def honeypot_remove(ctx, channel: discord.TextChannel):
    """Remove a honeypot channel."""
    db.execute("DELETE FROM honeypot WHERE guild_id=? AND channel_id=?", (ctx.guild.id, channel.id))
    try:
        await channel.set_permissions(ctx.guild.default_role, view_channel=True)
    except (discord.Forbidden, discord.HTTPException):
        pass
    await ctx.send(embed=bleed_embed("Honeypot Removed", f"{channel.mention} is no longer a honeypot."))

@honeypot_group.command(name="list")
async def honeypot_list(ctx):
    """List all active honeypot channels."""
    rows = db.fetchall("SELECT channel_id, punishment FROM honeypot WHERE guild_id=?", (ctx.guild.id,))
    if not rows:
        return await ctx.send(embed=bleed_embed("Honeypot Channels", "No honeypot channels configured."))
    msg = "\n".join([f"• <#{r[0]}> → **{r[1]}**" for r in rows])
    await ctx.send(embed=bleed_embed("Honeypot Channels", msg))

@honeypot_group.command(name="enable")
async def honeypot_enable(ctx):
    """Enable all honeypot channels (make them hidden again)."""
    rows = db.fetchall("SELECT channel_id FROM honeypot WHERE guild_id=?", (ctx.guild.id,))
    if not rows:
        return await ctx.send(embed=bleed_embed("Honeypot", "No honeypot channels configured."))
    cnt = 0
    for (ch_id,) in rows:
        ch = ctx.guild.get_channel(ch_id)
        if ch:
            try:
                await ch.set_permissions(ctx.guild.default_role, view_channel=False)
                cnt += 1
            except:
                pass
    await ctx.send(embed=bleed_embed("Honeypot", f"Enabled {cnt} honeypot channel(s)."))

@honeypot_group.command(name="disable")
async def honeypot_disable(ctx):
    """Disable all honeypot channels (make them visible but keep config)."""
    rows = db.fetchall("SELECT channel_id FROM honeypot WHERE guild_id=?", (ctx.guild.id,))
    if not rows:
        return await ctx.send(embed=bleed_embed("Honeypot", "No honeypot channels configured."))
    cnt = 0
    for (ch_id,) in rows:
        ch = ctx.guild.get_channel(ch_id)
        if ch:
            try:
                await ch.set_permissions(ctx.guild.default_role, view_channel=True)
                cnt += 1
            except:
                pass
    await ctx.send(embed=bleed_embed("Honeypot", f"Disabled {cnt} honeypot channel(s). Config preserved."))

@honeypot_group.command(name="config")
async def honeypot_config(ctx):
    """View honeypot system configuration."""
    rows = db.fetchall("SELECT channel_id, punishment FROM honeypot WHERE guild_id=?", (ctx.guild.id,))
    if not rows:
        return await ctx.send(embed=bleed_embed("Honeypot Config", "No honeypot channels configured."))
    embed = discord.Embed(title="Honeypot Configuration", color=0x9B59B6)
    embed.set_footer(text="bleed.bot • Honeypot")
    for ch_id, pun in rows:
        ch = ctx.guild.get_channel(ch_id)
        embed.add_field(
            name=f"{ch.name if ch else 'Unknown Channel'}",
            value=f"ID: `{ch_id}`\nPunishment: **{pun}**\nActive: {'Yes' if ch and not ch.permissions_for(ctx.guild.default_role).view_channel else 'No'}",
            inline=False
        )
    await ctx.send(embed=embed)


# ═══════════════════════════ CATEGORY 5: FAKE PERMISSIONS (6 commands) ═══════════════════════════

@bot.group(name="fakepermissions", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def fakepermissions_group(ctx):
    """Fake permissions — grant bleed-specific powers without Discord perms."""
    await ctx.send(embed=bleed_embed("Fake Permissions", "`add`, `remove`, `list`, `reset`, `check`, `export`"))

@fakepermissions_group.command(name="add")
async def fakepermissions_add(ctx, role: discord.Role, *, permission: str):
    """
    Grant a fake permission to a role.
    This gives bleed-specific abilities without granting Discord permissions.
    """
    db.execute(
        "INSERT OR IGNORE INTO fake_permissions VALUES (?,?,?)",
        (ctx.guild.id, role.id, permission.lower())
    )
    await ctx.send(embed=bleed_embed("Fake Permission Added", f"**{role.mention}** now has `{permission.lower()}` permissions in bleed."))

@fakepermissions_group.command(name="remove")
async def fakepermissions_remove(ctx, role: discord.Role, *, permission: str):
    """Revoke a fake permission from a role."""
    db.execute(
        "DELETE FROM fake_permissions WHERE guild_id=? AND role_id=? AND permission=?",
        (ctx.guild.id, role.id, permission.lower())
    )
    await ctx.send(embed=bleed_embed("Fake Permission Removed", f"Revoked `{permission.lower()}` from {role.mention}."))

@fakepermissions_group.command(name="list")
async def fakepermissions_list(ctx):
    """List all configured fake permissions."""
    rows = db.fetchall("SELECT role_id, permission FROM fake_permissions WHERE guild_id=? ORDER BY role_id", (ctx.guild.id,))
    if not rows:
        return await ctx.send(embed=bleed_embed("Fake Permissions", "No fake permissions configured."))
    
    # Group by role
    grouped = defaultdict(list)
    for role_id, perm in rows:
        grouped[role_id].append(perm)
    
    embed = discord.Embed(title="Fake Permissions", color=0x9B59B6)
    embed.set_footer(text="bleed.bot • Fake Permissions")
    for role_id, perms in grouped.items():
        role = ctx.guild.get_role(role_id)
        embed.add_field(
            name=f"{role.name if role else 'Unknown Role'}",
            value="\n".join([f"• `{p}`" for p in perms]),
            inline=False
        )
    await ctx.send(embed=embed)

@fakepermissions_group.command(name="reset")
async def fakepermissions_reset(ctx):
    """Reset all fake permissions for this server."""
    db.execute("DELETE FROM fake_permissions WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Fake Permissions Reset", "All fake permissions have been cleared."))

@fakepermissions_group.command(name="check")
async def fakepermissions_check(ctx, role: discord.Role):
    """Check which fake permissions a role has."""
    rows = db.fetchall("SELECT permission FROM fake_permissions WHERE guild_id=? AND role_id=?", (ctx.guild.id, role.id))
    if not rows:
        return await ctx.send(embed=bleed_embed(f"Permissions: {role.name}", "No fake permissions assigned."))
    perms = "\n".join([f"• `{r[0]}`" for r in rows])
    await ctx.send(embed=bleed_embed(f"Permissions: {role.name}", perms))

@fakepermissions_group.command(name="export")
async def fakepermissions_export(ctx):
    """Export all fake permissions as JSON."""
    rows = db.fetchall("SELECT role_id, permission FROM fake_permissions WHERE guild_id=?", (ctx.guild.id,))
    if not rows:
        return await ctx.send(embed=bleed_embed("Export", "No fake permissions to export."))
    
    data = {}
    for role_id, perm in rows:
        role = ctx.guild.get_role(role_id)
        role_name = role.name if role else str(role_id)
        if role_name not in data:
            data[role_name] = []
        data[role_name].append(perm)
    
    json_str = json.dumps(data, indent=2)
    if len(json_str) > 1900:
        # Send as file
        buffer = io.StringIO(json_str)
        await ctx.send(file=discord.File(buffer, filename="fake_permissions.json"))
    else:
        await ctx.send(embed=bleed_embed("Fake Permissions Export", f"```json\n{json_str}\n```"))
