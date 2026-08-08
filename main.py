# main.py — bleed.bot Clone Launcher
# github.com/burratapasta-commits/bleed
# python main.py

import os
import sys
import asyncio

# Check Python version
if sys.version_info < (3, 10):
    print("[FATAL] Python 3.10 or higher required.")
    sys.exit(1)

# Check for token
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    TOKEN = input("Enter your bot token: ").strip()
    if not TOKEN:
        print("[FATAL] No token provided. Set the TOKEN environment variable.")
        sys.exit(1)

# Check and install dependencies
try:
    import discord
    import aiohttp
except ImportError:
    print("[SETUP] Installing dependencies...")
    os.system(f"{sys.executable} -m pip install -r requirements.txt")
    print("[SETUP] Dependencies installed. Restarting...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

print("""
╔══════════════════════════════════════════╗
║         bleed.bot Clone v1.0             ║
║         408 Commands | 35 Categories      ║
║         github.com/burratapasta-commits   ║
╚══════════════════════════════════════════╝
""")

# Import and run the bot
try:
    from bleed_complete import bot, TOKEN as BOT_TOKEN
    
    # Override token if provided via env
    if os.environ.get("TOKEN"):
        import bleed_complete
        bleed_complete.TOKEN = os.environ.get("TOKEN")
    
    print(f"[MAIN] Starting bot with {len(bot.commands)} commands...")
    bot.run(TOKEN)
    
except ImportError as e:
    print(f"[FATAL] Could not import bleed_complete.py: {e}")
    print("[FATAL] Make sure bleed_complete.py is in the same directory.")
    sys.exit(1)
except discord.LoginFailure:
    print("[FATAL] Invalid bot token. Check your TOKEN.")
    sys.exit(1)
except Exception as e:
    print(f"[FATAL] {e}")
    sys.exit(1)
