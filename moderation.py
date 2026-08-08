# ═══════════════════════════ CATEGORY 1: MODERATION (45 commands) ═══════════════════════════

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_cmd(ctx):
    ow = {ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)}
    ch = await ctx.guild.create_text_channel("case-logs", overwrites=ow)
    jr = await ctx.guild.create_role(name="Jailed", color=discord.Color.dark_gray())
    mr = await ctx.guild.create_role(name="Muted", color=discord.Color.light_gray())
    db.execute("INSERT OR REPLACE INTO guild_config VALUES (?,?,?,?)", (ctx.guild.id, ch.id, jr.id, mr.id))
    for c in ctx.guild.channels:
        try: await c.set_permissions(jr, send_messages=False, speak=False); await c.set_permissions(mr, send_messages=False, speak=False, add_reactions=False)
        except: pass
    await ctx.send(embed=bleed_embed("Setup Complete", f"Logs: {ch.mention}\nJail: {jr.mention}\nMute: {mr.mention}"))

@bot.command(name="setupmute")
@commands.has_permissions(administrator=True)
async def setupmute_cmd(ctx):
    mr = await ctx.guild.create_role(name="Muted", color=discord.Color.light_gray())
    db.execute("UPDATE guild_config SET mute_role=? WHERE guild_id=?", (mr.id, ctx.guild.id))
    for c in ctx.guild.channels:
        try: await c.set_permissions(mr, send_messages=False, speak=False, add_reactions=False)
        except: pass
    await ctx.send(embed=bleed_embed("Setup Mute", f"{mr.mention}"))

@bot.command(name="bind")
@commands.has_permissions(administrator=True)
async def bind_cmd(ctx, option=None, target: discord.Role=None):
    if option != "staff": return await ctx.send(embed=error_embed("Usage: `,bind staff @role` or `,bind staff list`"))
    if target:
        r = db.fetchone("SELECT * FROM ticket_staff WHERE guild_id=? AND role_id=?", (ctx.guild.id, target.id))
        if r: db.execute("DELETE FROM ticket_staff WHERE guild_id=? AND role_id=?", (ctx.guild.id, target.id)); await ctx.send(embed=bleed_embed("Bind", f"{target.mention} removed."))
        else: db.execute("INSERT INTO ticket_staff VALUES (?,?)", (ctx.guild.id, target.id)); await ctx.send(embed=bleed_embed("Bind", f"{target.mention} added."))
    else:
        rows = db.fetchall("SELECT role_id FROM ticket_staff WHERE guild_id=?", (ctx.guild.id,))
        await ctx.send(embed=bleed_embed("Staff Roles", ", ".join([f"<@&{r[0]}>" for r in rows]) if rows else "None"))

@bot.command(name="invoke")
@commands.has_permissions(administrator=True)
async def invoke_cmd(ctx, cmd_name=None, mode=None, *, message=None):
    if not cmd_name or not mode or not message: return await ctx.send(embed=error_embed("Usage: `,invoke <cmd> message/dm <msg>`"))
    if mode == "message": db.execute("INSERT OR REPLACE INTO moderation_invoke (guild_id,command,message_response) VALUES (?,?,?)", (ctx.guild.id, cmd_name.lower(), message))
    elif mode == "dm": db.execute("INSERT OR REPLACE INTO moderation_invoke (guild_id,command,dm_response) VALUES (?,?,?)", (ctx.guild.id, cmd_name.lower(), message))
    else: return await ctx.send(embed=error_embed("Mode: `message` or `dm`."))
    await ctx.send(embed=bleed_embed("Invoke", f"Custom {mode} for `{cmd_name}` set."))

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_cmd(ctx, member: discord.Member, *, reason="No reason"):
    if not can_execute(ctx, member): return await ctx.send(embed=error_embed("Cannot ban."))
    cid = get_case_id(ctx.guild.id)
    try: await member.ban(reason=reason); db.execute("INSERT INTO cases (guild_id,case_type,user_id,moderator_id,reason,time) VALUES (?,?,?,?,?,?)", (ctx.guild.id,"ban",member.id,ctx.author.id,reason,time.time())); await ctx.send(embed=bleed_embed("Ban", f"{member} banned. Case #{cid}"))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="tempban")
@commands.has_permissions(ban_members=True)
async def tempban_cmd(ctx, member: discord.Member, duration="1d", *, reason="No reason"):
    secs = parse_duration(duration)
    if not secs: return await ctx.send(embed=error_embed("Invalid duration."))
    cid = get_case_id(ctx.guild.id)
    try:
        await member.ban(reason=f"Tempban: {reason}")
        db.execute("INSERT INTO cases (guild_id,case_type,user_id,moderator_id,reason,duration,time) VALUES (?,?,?,?,?,?,?)", (ctx.guild.id,"tempban",member.id,ctx.author.id,reason,secs,time.time()))
        await ctx.send(embed=bleed_embed("Tempban", f"{member} tempbanned {duration}. Case #{cid}"))
        await asyncio.sleep(secs)
        try: await ctx.guild.unban(member, reason="Tempban expired")
        except: pass
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="softban")
@commands.has_permissions(ban_members=True)
async def softban_cmd(ctx, member: discord.Member, *, reason="No reason"):
    if not can_execute(ctx, member): return await ctx.send(embed=error_embed("Cannot softban."))
    cid = get_case_id(ctx.guild.id)
    try: await member.ban(reason=reason, delete_message_days=7); await member.unban(reason="Softban complete"); db.execute("INSERT INTO cases (guild_id,case_type,user_id,moderator_id,reason,time) VALUES (?,?,?,?,?,?)", (ctx.guild.id,"softban",member.id,ctx.author.id,reason,time.time())); await ctx.send(embed=bleed_embed("Softban", f"{member} softbanned. Case #{cid}"))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="hardban")
@commands.has_permissions(ban_members=True)
async def hardban_cmd(ctx, member: discord.Member, *, reason="No reason"):
    if not can_execute(ctx, member): return await ctx.send(embed=error_embed("Cannot hardban."))
    cid = get_case_id(ctx.guild.id)
    try: await member.ban(reason=reason, delete_message_days=7); db.execute("INSERT INTO cases (guild_id,case_type,user_id,moderator_id,reason,time) VALUES (?,?,?,?,?,?)", (ctx.guild.id,"hardban",member.id,ctx.author.id,reason,time.time())); await ctx.send(embed=bleed_embed("Hardban", f"{member} hardbanned. Case #{cid}"))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban_cmd(ctx, user: discord.User, *, reason="No reason"):
    try: await ctx.guild.unban(user, reason=reason); await ctx.send(embed=bleed_embed("Unban", f"{user} unbanned."))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_cmd(ctx, member: discord.Member, *, reason="No reason"):
    if not can_execute(ctx, member): return await ctx.send(embed=error_embed("Cannot kick."))
    cid = get_case_id(ctx.guild.id)
    try: await member.kick(reason=reason); db.execute("INSERT INTO cases (guild_id,case_type,user_id,moderator_id,reason,time) VALUES (?,?,?,?,?,?)", (ctx.guild.id,"kick",member.id,ctx.author.id,reason,time.time())); await ctx.send(embed=bleed_embed("Kick", f"{member} kicked. Case #{cid}"))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="warn")
@commands.has_permissions(moderate_members=True)
async def warn_cmd(ctx, member: discord.Member, *, reason: str):
    cid = get_case_id(ctx.guild.id); n = time.time()
    db.execute("INSERT INTO warnings (guild_id,user_id,moderator_id,reason,time) VALUES (?,?,?,?,?)", (ctx.guild.id,member.id,ctx.author.id,reason,n))
    db.execute("INSERT INTO cases (guild_id,case_type,user_id,moderator_id,reason,time) VALUES (?,?,?,?,?,?)", (ctx.guild.id,"warn",member.id,ctx.author.id,reason,n))
    cnt = db.fetchone("SELECT COUNT(*) FROM warnings WHERE guild_id=? AND user_id=?", (ctx.guild.id,member.id))[0]
    await ctx.send(embed=bleed_embed("Warn", f"{member} warned (#{cnt}). Case #{cid}\n{reason}"))

@bot.command(name="timeout")
@commands.has_permissions(moderate_members=True)
async def timeout_cmd(ctx, member: discord.Member, duration="1h", *, reason="No reason"):
    secs = parse_duration(duration)
    if not secs or secs > 2419200: return await ctx.send(embed=error_embed("Invalid duration."))
    cid = get_case_id(ctx.guild.id); until = discord.utils.utcnow() + timedelta(seconds=secs)
    try: await member.timeout(until, reason=reason); db.execute("INSERT INTO cases (guild_id,case_type,user_id,moderator_id,reason,duration,time) VALUES (?,?,?,?,?,?,?)", (ctx.guild.id,"timeout",member.id,ctx.author.id,reason,secs,time.time())); await ctx.send(embed=bleed_embed("Timeout", f"{member} timed out {duration}. Case #{cid}"))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="mute")
@commands.has_permissions(moderate_members=True)
async def mute_cmd(ctx, member: discord.Member, duration="1h", *, reason="No reason"):
    r = db.fetchone("SELECT mute_role FROM guild_config WHERE guild_id=?", (ctx.guild.id,))
    if r and r[0]:
        role = ctx.guild.get_role(r[0])
        if role:
            try: await member.add_roles(role, reason=reason); await ctx.send(embed=bleed_embed("Mute", f"{member} muted via role.")); return
            except: pass
    secs = parse_duration(duration)
    if not secs or secs > 2419200: return await ctx.send(embed=error_embed("Invalid duration."))
    until = discord.utils.utcnow() + timedelta(seconds=secs)
    try: await member.timeout(until, reason=reason); await ctx.send(embed=bleed_embed("Mute", f"{member} muted {duration}."))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="unmute")
@commands.has_permissions(moderate_members=True)
async def unmute_cmd(ctx, member: discord.Member):
    r = db.fetchone("SELECT mute_role FROM guild_config WHERE guild_id=?", (ctx.guild.id,))
    if r and r[0]:
        role = ctx.guild.get_role(r[0])
        if role and role in member.roles:
            try: await member.remove_roles(role)
            except: pass
    try: await member.timeout(None)
    except: pass
    await ctx.send(embed=bleed_embed("Unmute", f"{member} unmuted."))

@bot.command(name="jail")
@commands.has_permissions(administrator=True)
async def jail_cmd(ctx, member: discord.Member, *, reason="No reason"):
    r = db.fetchone("SELECT jail_role FROM guild_config WHERE guild_id=?", (ctx.guild.id,))
    if not r or not r[0]: return await ctx.send(embed=error_embed("Run `,setup` first."))
    role = ctx.guild.get_role(r[0])
    if not role: return await ctx.send(embed=error_embed("Jail role missing."))
    cid = get_case_id(ctx.guild.id)
    try: await member.add_roles(role, reason=reason); db.execute("INSERT INTO cases (guild_id,case_type,user_id,moderator_id,reason,time) VALUES (?,?,?,?,?,?)", (ctx.guild.id,"jail",member.id,ctx.author.id,reason,time.time())); await ctx.send(embed=bleed_embed("Jail", f"{member} jailed. Case #{cid}"))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="unjail")
@commands.has_permissions(administrator=True)
async def unjail_cmd(ctx, member: discord.Member):
    r = db.fetchone("SELECT jail_role FROM guild_config WHERE guild_id=?", (ctx.guild.id,))
    if r and r[0]:
        role = ctx.guild.get_role(r[0])
        if role and role in member.roles:
            try: await member.remove_roles(role)
            except: pass
    await ctx.send(embed=bleed_embed("Unjail", f"{member} released."))

@bot.command(name="history")
@commands.has_permissions(moderate_members=True)
async def history_cmd(ctx, member: discord.Member):
    cases = db.fetchall("SELECT * FROM cases WHERE guild_id=? AND user_id=? ORDER BY time DESC LIMIT 20", (ctx.guild.id, member.id))
    if not cases: return await ctx.send(embed=bleed_embed("History", f"No history for {member}."))
    e = discord.Embed(title=f"History: {member}", color=0x9B59B6); e.set_footer(text="bleed.bot")
    for c in cases: e.add_field(name=f"#{c[0]} {c[2].title()}", value=f"Mod: <@{c[4]}>\n{c[5]}", inline=False)
    await ctx.send(embed=e)

@bot.command(name="cases")
@commands.has_permissions(moderate_members=True)
async def cases_cmd(ctx, member: discord.Member):
    cases = db.fetchall("SELECT * FROM cases WHERE guild_id=? AND user_id=? ORDER BY time DESC LIMIT 20", (ctx.guild.id, member.id))
    if not cases: return await ctx.send(embed=bleed_embed("Cases", f"No cases for {member}."))
    e = discord.Embed(title=f"Cases: {member}", color=0x9B59B6); e.set_footer(text="bleed.bot")
    for c in cases: e.add_field(name=f"#{c[0]} {c[2].title()}", value=f"Mod: <@{c[4]}>\n{c[5]}", inline=False)
    await ctx.send(embed=e)

@bot.command(name="case")
@commands.has_permissions(moderate_members=True)
async def case_cmd(ctx, case_id: int):
    case = next((c for c in db.fetchall("SELECT * FROM cases WHERE guild_id=?", (ctx.guild.id,)) if c[0] == case_id), None)
    if not case: return await ctx.send(embed=error_embed(f"Case #{case_id} not found."))
    e = discord.Embed(title=f"Case #{case_id} | {case[2].title()}", color=0x9B59B6, timestamp=datetime.fromtimestamp(case[7])); e.set_footer(text="bleed.bot")
    e.add_field(name="User", value=f"<@{case[3]}>", inline=True); e.add_field(name="Mod", value=f"<@{case[4]}>", inline=True)
    e.add_field(name="Reason", value=case[5] or "N/A", inline=False)
    if case[6]: e.add_field(name="Duration", value=format_duration(case[6]), inline=False)
    await ctx.send(embed=e)

@bot.command(name="reason")
@commands.has_permissions(moderate_members=True)
async def reason_cmd(ctx, case_id: int, *, reason: str):
    db.execute("UPDATE cases SET reason=? WHERE id=? AND guild_id=?", (reason, case_id, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Reason Updated", f"Case #{case_id}: {reason}"))

@bot.command(name="warns")
@commands.has_permissions(moderate_members=True)
async def warns_cmd(ctx, member: discord.Member):
    warns = db.fetchall("SELECT * FROM warnings WHERE guild_id=? AND user_id=? ORDER BY time DESC LIMIT 20", (ctx.guild.id, member.id))
    if not warns: return await ctx.send(embed=bleed_embed("Warnings", f"{member} has no warnings."))
    e = discord.Embed(title=f"Warnings: {member}", color=0xFFA500); e.set_footer(text="bleed.bot")
    for w in warns: e.add_field(name=f"#{w[0]} — {datetime.fromtimestamp(w[5]).strftime('%Y-%m-%d %H:%M')}", value=f"Mod: <@{w[3]}>\n{w[4]}", inline=False)
    await ctx.send(embed=e)

@bot.command(name="clearwarns")
@commands.has_permissions(administrator=True)
async def clearwarns_cmd(ctx, member: discord.Member):
    db.execute("DELETE FROM warnings WHERE guild_id=? AND user_id=?", (ctx.guild.id, member.id))
    await ctx.send(embed=bleed_embed("Clear Warnings", f"Cleared for {member}."))

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge_cmd(ctx, amount: int = 10):
    try:
        d = await ctx.channel.purge(limit=amount + 1)
        m = await ctx.send(embed=bleed_embed("Purge", f"Purged {len(d)-1} messages."))
        await asyncio.sleep(3); await m.delete()
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="slowmode")
@commands.has_permissions(manage_channels=True)
async def slowmode_cmd(ctx, seconds: int, channel: discord.TextChannel = None):
    ch = channel or ctx.channel; await ch.edit(slowmode_delay=max(0, min(21600, seconds)))
    await ctx.send(embed=bleed_embed("Slowmode", f"{ch.mention}: {ch.slowmode_delay}s"))

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel; await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=bleed_embed("Lock", f"{ch.mention} locked."))

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel; await ch.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(embed=bleed_embed("Unlock", f"{ch.mention} unlocked."))

@bot.command(name="lockall")
@commands.has_permissions(administrator=True)
async def lockall_cmd(ctx):
    for ch in ctx.guild.text_channels:
        try: await ch.set_permissions(ctx.guild.default_role, send_messages=False)
        except: pass
    await ctx.send(embed=bleed_embed("Lock All", "All channels locked."))

@bot.command(name="unlockall")
@commands.has_permissions(administrator=True)
async def unlockall_cmd(ctx):
    for ch in ctx.guild.text_channels:
        try: await ch.set_permissions(ctx.guild.default_role, send_messages=True)
        except: pass
    await ctx.send(embed=bleed_embed("Unlock All", "All channels unlocked."))

@bot.command(name="nuke")
@commands.has_permissions(administrator=True)
async def nuke_cmd(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel; pos = ch.position; nc = await ch.clone(); await ch.delete(); await nc.edit(position=pos)
    await nc.send(embed=bleed_embed("Nuke", "Channel nuked."))

@bot.command(name="roleall")
@commands.has_permissions(administrator=True)
async def roleall_cmd(ctx, role: discord.Role):
    cnt = 0
    for m in ctx.guild.members:
        if role not in m.roles:
            try: await m.add_roles(role); cnt += 1
            except: pass
    await ctx.send(embed=bleed_embed("Role All", f"{role.mention} added to {cnt} members."))

@bot.command(name="addrole")
@commands.has_permissions(manage_roles=True)
async def addrole_cmd(ctx, member: discord.Member, role: discord.Role):
    try: await member.add_roles(role); await ctx.send(embed=bleed_embed("Add Role", f"{role.mention} → {member}"))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="removerole")
@commands.has_permissions(manage_roles=True)
async def removerole_cmd(ctx, member: discord.Member, role: discord.Role):
    try: await member.remove_roles(role); await ctx.send(embed=bleed_embed("Remove Role", f"{role.mention} ✕ {member}"))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="forceremove")
@commands.has_permissions(administrator=True)
async def forceremove_cmd(ctx, member: discord.Member):
    roles = [r for r in member.roles if r.name != "@everyone"]
    for r in roles:
        try: await member.remove_roles(r)
        except: pass
    await ctx.send(embed=bleed_embed("Force Remove", f"Stripped {len(roles)} roles from {member}."))

@bot.command(name="nick")
@commands.has_permissions(manage_nicknames=True)
async def nick_cmd(ctx, member: discord.Member, *, nick: str = None):
    try: await member.edit(nick=nick); await ctx.send(embed=bleed_embed("Nickname", f"{'Reset' if not nick else 'Set'} for {member}."))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="stripstaff")
@commands.has_permissions(administrator=True)
async def stripstaff_cmd(ctx, member: discord.Member):
    rows = db.fetchall("SELECT role_id FROM ticket_staff WHERE guild_id=?", (ctx.guild.id,))
    cnt = 0
    for r in rows:
        role = ctx.guild.get_role(r[0])
        if role and role in member.roles:
            try: await member.remove_roles(role); cnt += 1
            except: pass
    await ctx.send(embed=bleed_embed("Strip Staff", f"Removed {cnt} staff roles from {member}."))

@bot.command(name="recentban")
@commands.has_permissions(moderate_members=True)
async def recentban_cmd(ctx):
    try:
        bans = [e async for e in ctx.guild.bans(limit=10)]
        if not bans: return await ctx.send(embed=bleed_embed("Recent Bans", "No bans."))
        await ctx.send(embed=bleed_embed("Recent Bans", "\n".join(f"**{e.user}** — {e.reason or 'No reason'}" for e in bans)))
    except Exception as e: await ctx.send(embed=error_embed(str(e)))

@bot.command(name="raid")
@commands.has_permissions(administrator=True)
async def raid_cmd(ctx, action: str = "lockdown"):
    if action == "lockdown":
        for ch in ctx.guild.text_channels:
            try: await ch.set_permissions(ctx.guild.default_role, send_messages=False)
            except: pass
        await ctx.send(embed=bleed_embed("Raid Lockdown", "All channels locked."))
    elif action == "unlock":
        for ch in ctx.guild.text_channels:
            try: await ch.set_permissions(ctx.guild.default_role, send_messages=True)
            except: pass
        await ctx.send(embed=bleed_embed("Raid Unlock", "All channels unlocked."))

@bot.command(name="massban")
@commands.has_permissions(ban_members=True)
async def massban_cmd(ctx, *members: discord.Member):
    cnt = 0
    for m in members:
        try: await m.ban(reason="Mass ban"); cnt += 1
        except: pass
    await ctx.send(embed=bleed_embed("Mass Ban", f"Banned {cnt}/{len(members)} members."))

@bot.command(name="masskick")
@commands.has_permissions(kick_members=True)
async def masskick_cmd(ctx, *members: discord.Member):
    cnt = 0
    for m in members:
        try: await m.kick(reason="Mass kick"); cnt += 1
        except: pass
    await ctx.send(embed=bleed_embed("Mass Kick", f"Kicked {cnt}/{len(members)} members."))

@bot.command(name="massmute")
@commands.has_permissions(moderate_members=True)
async def massmute_cmd(ctx, *members: discord.Member):
    cnt = 0
    for m in members:
        try: await m.timeout(discord.utils.utcnow() + timedelta(hours=1), reason="Mass mute"); cnt += 1
        except: pass
    await ctx.send(embed=bleed_embed("Mass Mute", f"Muted {cnt}/{len(members)} members."))

@bot.command(name="massunmute")
@commands.has_permissions(moderate_members=True)
async def massunmute_cmd(ctx, *members: discord.Member):
    cnt = 0
    for m in members:
        try: await m.timeout(None); cnt += 1
        except: pass
    await ctx.send(embed=bleed_embed("Mass Unmute", f"Unmuted {cnt}/{len(members)} members."))

@bot.command(name="warnconfig")
@commands.has_permissions(administrator=True)
async def warnconfig_cmd(ctx, threshold: int = None, action: str = None):
    cfg = {"threshold": threshold or 5, "action": action or "ban"}
    await ctx.send(embed=bleed_embed("Warn Config", f"Threshold: {cfg['threshold']}\nAction: {cfg['action']}"))
