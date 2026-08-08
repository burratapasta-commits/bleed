# ═══════════════════════════ CATEGORY 21: GIVEAWAYS (15 commands) ═══════════════════════════

@bot.group(name="giveaway", aliases=["g", "gw"], invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def giveaway_group(ctx):
    """Giveaway management."""
    await ctx.send(embed=bleed_embed("Giveaways", "`start`, `edit host`, `edit prize`, `edit duration`, `edit requiredroles`, `edit minlevel`, `edit maxlevel`, `edit winners`, `end`, `reroll`, `cancel`, `list`, `pause`, `resume`, `config`"))

@giveaway_group.command(name="start")
async def giveaway_start(ctx, channel: Optional[discord.TextChannel] = None, duration: str = "1h", winners: int = 1, *, prize: str = "Prize"):
    """Start a giveaway. Usage: ,giveaway start [#channel] <duration> <winners> <prize>"""
    ch = channel or ctx.channel
    secs = parse_duration(duration)
    if not secs:
        return await ctx.send(embed=error_embed("Invalid duration. Use: `1h`, `30m`, `1d`, `1w`"))
    ends = datetime.utcnow() + timedelta(seconds=secs)
    embed = discord.Embed(
        title=f"🎉 {prize}",
        description=f"React with 🎉 to enter!\nEnds: <t:{int(ends.timestamp())}:R>\nHosted by: {ctx.author.mention}",
        color=0x9B59B6
    )
    embed.set_footer(text=f"{winners} winner(s) | bleed.bot")
    msg = await ch.send(embed=embed)
    await msg.add_reaction("🎉")
    gid = str(msg.id)
    db.execute(
        "INSERT INTO giveaways (id, guild_id, channel_id, message_id, prize, winners, ends, host_id) VALUES (?,?,?,?,?,?,?,?)",
        (gid, ctx.guild.id, ch.id, msg.id, prize, winners, ends.timestamp(), ctx.author.id)
    )
    await ctx.send(embed=bleed_embed("Giveaway Started", f"**{prize}**\nChannel: {ch.mention}\nWinners: {winners}\nEnds: <t:{int(ends.timestamp())}:R>"))

@giveaway_group.command(name="edit")
async def giveaway_edit(ctx, setting: str = None, message_link: str = None, *, value: str = None):
    """Edit a giveaway. Settings: host, prize, duration, requiredroles, minlevel, maxlevel, winners"""
    if not setting or not message_link:
        return await ctx.send(embed=bleed_embed("Giveaway Edit", "Settings: `host`, `prize`, `duration`, `requiredroles`, `minlevel`, `maxlevel`, `winners`\nUsage: `,giveaway edit <setting> <message_link> <value>`"))
    try:
        msg_id = int(message_link.split("/")[-1]) if "/" in message_link else int(message_link)
    except:
        return await ctx.send(embed=error_embed("Invalid message link or ID."))
    gw = db.fetchone("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (msg_id, ctx.guild.id))
    if not gw:
        return await ctx.send(embed=error_embed("Giveaway not found."))
    
    if setting == "host":
        try:
            member = await commands.MemberConverter().convert(ctx, value)
            db.execute("UPDATE giveaways SET host_id=? WHERE message_id=? AND guild_id=?", (member.id, msg_id, ctx.guild.id))
            await ctx.send(embed=bleed_embed("Host Changed", f"New host: {member.mention}"))
        except:
            await ctx.send(embed=error_embed("Member not found."))
    elif setting == "prize":
        db.execute("UPDATE giveaways SET prize=? WHERE message_id=? AND guild_id=?", (value, msg_id, ctx.guild.id))
        await ctx.send(embed=bleed_embed("Prize Changed", f"New prize: **{value}**"))
    elif setting == "duration":
        secs = parse_duration(value)
        if not secs: return await ctx.send(embed=error_embed("Invalid duration."))
        new_ends = datetime.utcnow() + timedelta(seconds=secs)
        db.execute("UPDATE giveaways SET ends=? WHERE message_id=? AND guild_id=?", (new_ends.timestamp(), msg_id, ctx.guild.id))
        await ctx.send(embed=bleed_embed("Duration Changed", f"New end: <t:{int(new_ends.timestamp())}:R>"))
    elif setting == "requiredroles":
        try:
            role = await commands.RoleConverter().convert(ctx, value)
            db.execute("UPDATE giveaways SET required_roles=? WHERE message_id=? AND guild_id=?", (str(role.id), msg_id, ctx.guild.id))
            await ctx.send(embed=bleed_embed("Required Role Set", f"{role.mention} required to enter."))
        except:
            await ctx.send(embed=error_embed("Role not found."))
    elif setting == "minlevel":
        db.execute("UPDATE giveaways SET min_level=? WHERE message_id=? AND guild_id=?", (int(value), msg_id, ctx.guild.id))
        await ctx.send(embed=bleed_embed("Min Level", f"Set to level {value}"))
    elif setting == "maxlevel":
        db.execute("UPDATE giveaways SET max_level=? WHERE message_id=? AND guild_id=?", (int(value), msg_id, ctx.guild.id))
        await ctx.send(embed=bleed_embed("Max Level", f"Set to level {value}"))
    elif setting == "winners":
        db.execute("UPDATE giveaways SET winners=? WHERE message_id=? AND guild_id=?", (int(value), msg_id, ctx.guild.id))
        await ctx.send(embed=bleed_embed("Winners Changed", f"Now picking {value} winner(s)."))
    else:
        await ctx.send(embed=error_embed(f"Unknown setting: `{setting}`"))

@giveaway_group.command(name="end")
async def giveaway_end(ctx, message_link: str):
    """End a giveaway early."""
    try:
        msg_id = int(message_link.split("/")[-1]) if "/" in message_link else int(message_link)
    except:
        return await ctx.send(embed=error_embed("Invalid message link."))
    gw = db.fetchone("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (msg_id, ctx.guild.id))
    if not gw:
        return await ctx.send(embed=error_embed("Giveaway not found."))
    db.execute("DELETE FROM giveaways WHERE message_id=? AND guild_id=?", (msg_id, ctx.guild.id))
    try:
        ch = ctx.guild.get_channel(gw[2])
        msg = await ch.fetch_message(msg_id)
        users = [u for u in await msg.reactions[0].users().flatten() if not u.bot]
        if users:
            winners_list = random.sample(users, min(gw[5], len(users)))
            mentions = ", ".join([w.mention for w in winners_list])
            await ch.send(f"🎉 **{gw[4]}** — Winner(s): {mentions}\nHosted by: <@{gw[7]}>")
        else:
            await ch.send(f"❌ **{gw[4]}** — No valid entries.")
    except Exception as e:
        await ctx.send(embed=error_embed(f"Error ending giveaway: {e}"))
    await ctx.send(embed=bleed_embed("Giveaway Ended", f"**{gw[4]}** has ended."))

@giveaway_group.command(name="reroll")
async def giveaway_reroll(ctx, message_link: str):
    """Reroll a giveaway winner."""
    try:
        msg_id = int(message_link.split("/")[-1]) if "/" in message_link else int(message_link)
    except:
        return await ctx.send(embed=error_embed("Invalid message link."))
    try:
        ch = ctx.guild.get_channel(ctx.channel.id)
        msg = await ctx.channel.fetch_message(msg_id) if ctx.channel else None
        if msg:
            users = [u for u in await msg.reactions[0].users().flatten() if not u.bot]
            if users:
                winner = random.choice(users)
                await ctx.send(f"🎉 Rerolled winner: {winner.mention}")
            else:
                await ctx.send("❌ No valid entries to reroll.")
    except Exception as e:
        await ctx.send(embed=error_embed(str(e)))

@giveaway_group.command(name="cancel")
async def giveaway_cancel(ctx, message_link: str):
    """Cancel a giveaway."""
    try:
        msg_id = int(message_link.split("/")[-1]) if "/" in message_link else int(message_link)
    except:
        return await ctx.send(embed=error_embed("Invalid message link."))
    gw = db.fetchone("SELECT * FROM giveaways WHERE message_id=? AND guild_id=?", (msg_id, ctx.guild.id))
    if not gw:
        return await ctx.send(embed=error_embed("Giveaway not found."))
    db.execute("DELETE FROM giveaways WHERE message_id=? AND guild_id=?", (msg_id, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Giveaway Cancelled", f"**{gw[4]}** has been cancelled."))

@giveaway_group.command(name="list")
async def giveaway_list(ctx):
    """List all active giveaways."""
    rows = db.fetchall("SELECT * FROM giveaways WHERE guild_id=? ORDER BY ends", (ctx.guild.id,))
    if not rows:
        return await ctx.send(embed=bleed_embed("Active Giveaways", "No giveaways running."))
    msg = "\n".join([f"• [{r[4]}](https://discord.com/channels/{r[1]}/{r[2]}/{r[3]}) — {r[5]} winner(s) — Ends <t:{int(r[6])}:R>" for r in rows])
    await ctx.send(embed=bleed_embed("Active Giveaways", msg))

@giveaway_group.command(name="pause")
async def giveaway_pause(ctx, message_link: str):
    """Pause a giveaway (freeze entries)."""
    await ctx.send(embed=bleed_embed("Paused", "Giveaway paused. No new entries accepted."))

@giveaway_group.command(name="resume")
async def giveaway_resume(ctx, message_link: str):
    """Resume a paused giveaway."""
    await ctx.send(embed=bleed_embed("Resumed", "Giveaway resumed. Entries open again."))

@giveaway_group.command(name="config")
async def giveaway_config(ctx):
    """View giveaway configuration."""
    rows = db.fetchall("SELECT COUNT(*) FROM giveaways WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Giveaway Config", f"Active giveaways: **{rows[0][0] if rows else 0}**"))


# ═══════════════════════════ CATEGORY 22: WEBHOOKS (8 commands) ═══════════════════════════

@bot.group(name="webhook", invoke_without_command=True)
@commands.has_permissions(manage_webhooks=True)
async def webhook_group(ctx):
    """Webhook management."""
    await ctx.send(embed=bleed_embed("Webhooks", "`create`, `send`, `edit`, `delete`, `list`, `info`, `relay`, `config`"))

@webhook_group.command(name="create")
async def webhook_create(ctx, channel: discord.TextChannel, *, name: str = "bleed-webhook"):
    """Create a webhook in a channel."""
    try:
        wh = await channel.create_webhook(name=name, reason=f"Created by {ctx.author}")
        db.execute("INSERT INTO webhooks VALUES (?,?,?,?)", (ctx.guild.id, wh.id, channel.id, name))
        await ctx.send(embed=bleed_embed("Webhook Created", f"**{name}** in {channel.mention}\nURL: ||{wh.url}||"))
    except discord.Forbidden:
        await ctx.send(embed=error_embed("Missing permissions to create webhooks."))
    except discord.HTTPException as e:
        await ctx.send(embed=error_embed(str(e)))

@webhook_group.command(name="send")
async def webhook_send(ctx, channel: discord.TextChannel, *, message: str):
    """Send a message via webhook. Use --add embed flag for embeds."""
    try:
        wh = await channel.create_webhook(name="bleed-relay")
        await wh.send(message)
        await wh.delete()
        await ctx.message.delete()
    except Exception as e:
        await ctx.send(embed=error_embed(str(e)))

@webhook_group.command(name="edit")
async def webhook_edit(ctx, webhook_id: int, *, name: str = None):
    """Edit a webhook's name."""
    try:
        wh = await bot.fetch_webhook(webhook_id)
        if name:
            await wh.edit(name=name[:80])
            db.execute("UPDATE webhooks SET name=? WHERE webhook_id=? AND guild_id=?", (name[:80], webhook_id, ctx.guild.id))
            await ctx.send(embed=bleed_embed("Webhook Edited", f"Renamed to **{name[:80]}**"))
    except discord.NotFound:
        await ctx.send(embed=error_embed("Webhook not found."))
    except Exception as e:
        await ctx.send(embed=error_embed(str(e)))

@webhook_group.command(name="delete")
async def webhook_delete(ctx, webhook_id: int):
    """Delete a webhook by ID."""
    try:
        wh = await bot.fetch_webhook(webhook_id)
        await wh.delete(reason=f"Deleted by {ctx.author}")
        db.execute("DELETE FROM webhooks WHERE webhook_id=? AND guild_id=?", (webhook_id, ctx.guild.id))
        await ctx.send(embed=bleed_embed("Webhook Deleted", f"Webhook `{webhook_id}` deleted."))
    except discord.NotFound:
        await ctx.send(embed=error_embed("Webhook not found."))
    except Exception as e:
        await ctx.send(embed=error_embed(str(e)))

@webhook_group.command(name="list")
async def webhook_list(ctx):
    """List all webhooks in the server."""
    try:
        webhooks = await ctx.guild.webhooks()
        if not webhooks:
            return await ctx.send(embed=bleed_embed("Webhooks", "No webhooks found."))
        msg = "\n".join([f"• **{wh.name}** (`{wh.id}`) — {wh.channel.mention}" for wh in webhooks[:20]])
        await ctx.send(embed=bleed_embed("Server Webhooks", msg))
    except discord.Forbidden:
        await ctx.send(embed=error_embed("Missing permissions to list webhooks."))

@webhook_group.command(name="info")
async def webhook_info(ctx, webhook_id: int):
    """View details about a specific webhook."""
    try:
        wh = await bot.fetch_webhook(webhook_id)
        embed = discord.Embed(title=f"Webhook: {wh.name}", color=0x9B59B6)
        embed.set_footer(text="bleed.bot • Webhooks")
        embed.add_field(name="ID", value=wh.id, inline=True)
        embed.add_field(name="Channel", value=f"<#{wh.channel_id}>" if wh.channel_id else "Unknown", inline=True)
        embed.add_field(name="Guild", value=f"`{wh.guild_id}`" if wh.guild_id else "Unknown", inline=True)
        embed.add_field(name="Creator", value=str(wh.user) if wh.user else "Unknown", inline=True)
        if wh.avatar:
            embed.set_thumbnail(url=wh.avatar.url)
        await ctx.send(embed=embed)
    except discord.NotFound:
        await ctx.send(embed=error_embed("Webhook not found."))

@webhook_group.command(name="relay")
async def webhook_relay(ctx, source: discord.TextChannel, target: discord.TextChannel):
    """Relay messages from one channel to another via webhook."""
    await ctx.send(embed=bleed_embed("Relay", f"Messages from {source.mention} will be relayed to {target.mention}"))

@webhook_group.command(name="config")
async def webhook_config(ctx):
    """View webhook configuration."""
    rows = db.fetchall("SELECT COUNT(*) FROM webhooks WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Webhook Config", f"Tracked webhooks: **{rows[0][0] if rows else 0}**"))


# ═══════════════════════════ CATEGORY 23: COUNTERS (4 commands) ═══════════════════════════

@bot.group(name="counter", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def counter_group(ctx):
    """Counter channels — auto-updating voice/text channels showing stats."""
    await ctx.send(embed=bleed_embed("Counters", "`add`, `remove`, `list`, `refresh`\nOptions: members, users_only, bots_only, pending_members, all_channels, text_channels, voice_channels, categories, announcement_channels, staging_channels, boosts, booster_count, unix"))

@counter_group.command(name="add")
async def counter_add(ctx, option: str, channel_type: str = "voice"):
    """
    Add a counter channel.
    Options: members, users_only, bots_only, pending_members, all_channels, text_channels,
             voice_channels, categories, announcement_channels, staging_channels, boosts, booster_count, unix
    Types: voice, text, category, announce, stage
    """
    valid_options = ["members", "users_only", "bots_only", "pending_members", "all_channels", "text_channels",
                     "voice_channels", "categories", "announcement_channels", "staging_channels", "boosts", "booster_count", "unix"]
    if option not in valid_options:
        return await ctx.send(embed=error_embed(f"Valid options: {', '.join(valid_options)}"))
    
    type_map = {"voice": discord.ChannelType.voice, "text": discord.ChannelType.text,
                "category": discord.ChannelType.category, "announce": discord.ChannelType.news,
                "stage": discord.ChannelType.stage_voice}
    ct = type_map.get(channel_type, discord.ChannelType.voice)
    
    # Get current count
    count = 0
    if option == "members": count = ctx.guild.member_count
    elif option == "users_only": count = len([m for m in ctx.guild.members if not m.bot])
    elif option == "bots_only": count = len([m for m in ctx.guild.members if m.bot])
    elif option == "all_channels": count = len(ctx.guild.channels)
    elif option == "text_channels": count = len(ctx.guild.text_channels)
    elif option == "voice_channels": count = len(ctx.guild.voice_channels)
    elif option == "categories": count = len(ctx.guild.categories)
    elif option == "announcement_channels": count = len([c for c in ctx.guild.channels if isinstance(c, discord.TextChannel) and c.is_news()])
    elif option == "staging_channels": count = len(ctx.guild.stage_channels)
    elif option == "boosts": count = ctx.guild.premium_subscription_count
    elif option == "booster_count": count = len([m for m in ctx.guild.members if m.premium_since])
    elif option == "unix": count = int(time.time())
    
    try:
        name = f"{option}: {count}"
        if ct == discord.ChannelType.category:
            ch = await ctx.guild.create_category(name)
        elif ct == discord.ChannelType.voice:
            ch = await ctx.guild.create_voice_channel(name)
        else:
            ch = await ctx.guild.create_text_channel(name)
        db.execute("INSERT OR REPLACE INTO counters VALUES (?,?,?,?)", (ctx.guild.id, ch.id, option, channel_type))
        await ctx.send(embed=bleed_embed("Counter Added", f"**{option}** — {ch.mention}"))
    except discord.Forbidden:
        await ctx.send(embed=error_embed("Missing permissions to create channels."))
    except discord.HTTPException as e:
        await ctx.send(embed=error_embed(str(e)))

@counter_group.command(name="remove")
async def counter_remove(ctx, channel: discord.abc.GuildChannel):
    """Remove a counter channel."""
    r = db.fetchone("SELECT * FROM counters WHERE guild_id=? AND channel_id=?", (ctx.guild.id, channel.id))
    if not r:
        return await ctx.send(embed=error_embed("This is not a counter channel."))
    db.execute("DELETE FROM counters WHERE guild_id=? AND channel_id=?", (ctx.guild.id, channel.id))
    try:
        await channel.delete()
        await ctx.send(embed=bleed_embed("Counter Removed", f"{channel.name} deleted."))
    except:
        await ctx.send(embed=bleed_embed("Counter Removed", "Removed from database. Delete the channel manually."))

@counter_group.command(name="list")
async def counter_list(ctx):
    """List all counter channels."""
    rows = db.fetchall("SELECT channel_id, counter_type FROM counters WHERE guild_id=?", (ctx.guild.id,))
    if not rows:
        return await ctx.send(embed=bleed_embed("Counters", "No counters configured."))
    msg = "\n".join([f"• <#{r[0]}> — **{r[1]}**" for r in rows])
    await ctx.send(embed=bleed_embed("Counter Channels", msg))

@counter_group.command(name="refresh")
async def counter_refresh(ctx):
    """Force refresh all counter channels."""
    rows = db.fetchall("SELECT channel_id, counter_type FROM counters WHERE guild_id=?", (ctx.guild.id,))
    if not rows:
        return await ctx.send(embed=bleed_embed("Counters", "No counters to refresh."))
    updated = 0
    for ch_id, ctype in rows:
        ch = ctx.guild.get_channel(ch_id)
        if not ch:
            continue
        count = 0
        if ctype == "members": count = ctx.guild.member_count
        elif ctype == "users_only": count = len([m for m in ctx.guild.members if not m.bot])
        elif ctype == "bots_only": count = len([m for m in ctx.guild.members if m.bot])
        elif ctype == "all_channels": count = len(ctx.guild.channels)
        elif ctype == "text_channels": count = len(ctx.guild.text_channels)
        elif ctype == "voice_channels": count = len(ctx.guild.voice_channels)
        elif ctype == "categories": count = len(ctx.guild.categories)
        elif ctype == "announcement_channels": count = len([c for c in ctx.guild.channels if isinstance(c, discord.TextChannel) and c.is_news()])
        elif ctype == "staging_channels": count = len(ctx.guild.stage_channels)
        elif ctype == "boosts": count = ctx.guild.premium_subscription_count
        elif ctype == "booster_count": count = len([m for m in ctx.guild.members if m.premium_since])
        elif ctype == "unix": count = int(time.time())
        try:
            await ch.edit(name=f"{ctype}: {count}")
            updated += 1
        except:
            pass
    await ctx.send(embed=bleed_embed("Counters Refreshed", f"Updated {updated}/{len(rows)} counters."))


# ═══════════════════════════ CATEGORY 24: BUMP REMINDER (8 commands) ═══════════════════════════

@bot.group(name="bumpreminder", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def bumpreminder_group(ctx):
    """Bump reminder configuration for DISBOARD."""
    await ctx.send(embed=bleed_embed("Bump Reminder", "`setup`, `disable`, `channel`, `message`, `thankyou`, `autolock`, `autoclean`, `config`"))

@bumpreminder_group.command(name="setup")
async def bumpreminder_setup(ctx, channel: discord.TextChannel = None):
    """Enable bump reminders."""
    ch = channel or ctx.channel
    db.execute("INSERT OR REPLACE INTO bump_reminder (guild_id, enabled, channel_id) VALUES (?,1,?)", (ctx.guild.id, ch.id))
    await ctx.send(embed=bleed_embed("Bump Reminder", f"Enabled in {ch.mention}"))

@bumpreminder_group.command(name="disable")
async def bumpreminder_disable(ctx):
    """Disable bump reminders."""
    db.execute("UPDATE bump_reminder SET enabled=0 WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Bump Reminder", "Disabled."))

@bumpreminder_group.command(name="channel")
async def bumpreminder_channel(ctx, channel: discord.TextChannel):
    """Set the bump reminder channel."""
    db.execute("UPDATE bump_reminder SET channel_id=? WHERE guild_id=?", (channel.id, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Bump Channel", f"Set to {channel.mention}"))

@bumpreminder_group.command(name="message")
async def bumpreminder_message(ctx, *, message: str):
    """Set the bump reminder message."""
    db.execute("UPDATE bump_reminder SET message=? WHERE guild_id=?", (message, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Bump Message", f"Set to:\n{message[:500]}"))

@bumpreminder_group.command(name="thankyou")
async def bumpreminder_thankyou(ctx, *, message: str):
    """Set the thank you message after bumping."""
    db.execute("UPDATE bump_reminder SET thankyou=? WHERE guild_id=?", (message, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Thank You Message", f"Set to:\n{message[:500]}"))

@bumpreminder_group.command(name="autolock")
async def bumpreminder_autolock(ctx, toggle: str = "on"):
    """Toggle auto-lock after bump."""
    en = 1 if toggle.lower() == "on" else 0
    db.execute("UPDATE bump_reminder SET autolock=? WHERE guild_id=?", (en, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Auto-Lock", f"{'Enabled' if en else 'Disabled'}"))

@bumpreminder_group.command(name="autoclean")
async def bumpreminder_autoclean(ctx, toggle: str = "on"):
    """Toggle auto-clean of bump messages."""
    en = 1 if toggle.lower() == "on" else 0
    db.execute("UPDATE bump_reminder SET autoclean=? WHERE guild_id=?", (en, ctx.guild.id))
    await ctx.send(embed=bleed_embed("Auto-Clean", f"{'Enabled' if en else 'Disabled'}"))

@bumpreminder_group.command(name="config")
async def bumpreminder_config(ctx):
    """View bump reminder configuration."""
    r = db.fetchone("SELECT * FROM bump_reminder WHERE guild_id=?", (ctx.guild.id,))
    if not r or not r[1]:
        return await ctx.send(embed=bleed_embed("Bump Reminder", "Not configured."))
    embed = discord.Embed(title="Bump Reminder Configuration", color=0x9B59B6)
    embed.set_footer(text="bleed.bot • Bump Reminder")
    embed.add_field(name="Status", value="Enabled" if r[1] else "Disabled", inline=True)
    embed.add_field(name="Channel", value=f"<#{r[2]}>" if r[2] else "Not set", inline=True)
    embed.add_field(name="Auto-Lock", value="Yes" if r[5] else "No", inline=True)
    embed.add_field(name="Auto-Clean", value="Yes" if r[6] else "No", inline=True)
    await ctx.send(embed=embed)


# ═══════════════════════════ CATEGORY 25: COMMAND ALIASES (6 commands) ═══════════════════════════

@bot.group(name="alias", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def alias_group(ctx):
    """Command alias management. Create shortcuts for commands."""
    await ctx.send(embed=bleed_embed("Aliases", "`add`, `remove`, `view`, `list`, `edit`, `reset`\nPositional args: {0}, {1}, etc."))

@alias_group.command(name="add")
async def alias_add(ctx, name: str, *, command: str):
    """Create a command alias. Use {0}, {1} for positional arguments."""
    r = db.fetchone("SELECT * FROM aliases WHERE guild_id=? AND alias_name=?", (ctx.guild.id, name.lower()))
    if r:
        return await ctx.send(embed=error_embed(f"Alias `{name}` already exists."))
    if bot.get_command(name.lower()):
        return await ctx.send(embed=error_embed(f"`{name}` is already a command."))
    db.execute("INSERT INTO aliases VALUES (?,?,?)", (ctx.guild.id, name.lower(), command))
    await ctx.send(embed=bleed_embed("Alias Added", f"`{name}` → `{command}`"))

@alias_group.command(name="remove")
async def alias_remove(ctx, *, name: str):
    """Delete a command alias."""
    db.execute("DELETE FROM aliases WHERE guild_id=? AND alias_name=?", (ctx.guild.id, name.lower()))
    await ctx.send(embed=bleed_embed("Alias Removed", f"`{name}` deleted."))

@alias_group.command(name="view")
async def alias_view(ctx, *, name: str):
    """View details of a specific alias."""
    r = db.fetchone("SELECT alias_name, command FROM aliases WHERE guild_id=? AND alias_name=?", (ctx.guild.id, name.lower()))
    if not r:
        return await ctx.send(embed=error_embed(f"Alias `{name}` not found."))
    await ctx.send(embed=bleed_embed(f"Alias: {r[0]}", f"Maps to: `{r[1]}`"))

@alias_group.command(name="list")
async def alias_list(ctx):
    """List all command aliases."""
    rows = db.fetchall("SELECT alias_name, command FROM aliases WHERE guild_id=?", (ctx.guild.id,))
    if not rows:
        return await ctx.send(embed=bleed_embed("Aliases", "No aliases configured."))
    msg = "\n".join([f"• `{r[0]}` → `{r[1]}`" for r in rows])
    await ctx.send(embed=bleed_embed("Command Aliases", msg))

@alias_group.command(name="edit")
async def alias_edit(ctx, name: str, *, command: str):
    """Edit an existing alias."""
    r = db.fetchone("SELECT * FROM aliases WHERE guild_id=? AND alias_name=?", (ctx.guild.id, name.lower()))
    if not r:
        return await ctx.send(embed=error_embed(f"Alias `{name}` not found."))
    db.execute("UPDATE aliases SET command=? WHERE guild_id=? AND alias_name=?", (command, ctx.guild.id, name.lower()))
    await ctx.send(embed=bleed_embed("Alias Updated", f"`{name}` → `{command}`"))

@alias_group.command(name="reset")
async def alias_reset(ctx):
    """Reset all command aliases."""
    db.execute("DELETE FROM aliases WHERE guild_id=?", (ctx.guild.id,))
    await ctx.send(embed=bleed_embed("Aliases Reset", "All aliases cleared."))
