import asyncio
import logging
import os
import sys

import aiohttp
import discord
from aiohttp import web
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("premium_bot")

TOKEN = os.getenv("DISCORD_TOKEN", "").strip().strip('"').strip("'")
PREMIUM_PASSWORD = os.getenv("PREMIUM_PASSWORD", "").strip()
PREMIUM_ROLE_NAME = "Premium"
BUTTON_CUSTOM_ID = "premium_role_button"
PORT = int(os.getenv("PORT", "10000"))
KEEP_ALIVE_INTERVAL = 14 * 60  # Render free tier sleeps after ~15 min idle


def get_keep_alive_url() -> str | None:
    render_url = os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
    if render_url:
        return f"{render_url}/health"
    custom_url = os.getenv("KEEP_ALIVE_URL", "").strip()
    return custom_url or None


async def grant_premium_role(interaction: discord.Interaction) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "This only works inside a server.", ephemeral=True
        )
        return

    member = interaction.user
    if not isinstance(member, discord.Member):
        await interaction.response.send_message(
            "Could not find your member profile.", ephemeral=True
        )
        return

    premium_role = discord.utils.get(interaction.guild.roles, name=PREMIUM_ROLE_NAME)
    if premium_role is None:
        await interaction.response.send_message(
            f"The **{PREMIUM_ROLE_NAME}** role was not found. Ask an admin to create it.",
            ephemeral=True,
        )
        return

    if premium_role in member.roles:
        await interaction.response.send_message(
            "You already have the Premium role.", ephemeral=True
        )
        return

    bot_member = interaction.guild.me
    if bot_member is None or premium_role >= bot_member.top_role:
        await interaction.response.send_message(
            "I cannot assign that role. Move my bot role above the Premium role in Server Settings.",
            ephemeral=True,
        )
        return

    try:
        await member.add_roles(premium_role, reason="Premium password verified")
    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to assign the Premium role.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        "Premium role granted. You can now see the Premium Workflow channels.",
        ephemeral=True,
    )


class PremiumPasswordModal(discord.ui.Modal, title="Premium Access"):
    password = discord.ui.TextInput(
        label="Password",
        placeholder="Enter the premium access password",
        required=True,
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not PREMIUM_PASSWORD:
            await interaction.response.send_message(
                "Premium password is not configured. Ask an admin to fix the bot.",
                ephemeral=True,
            )
            return

        if self.password.value != PREMIUM_PASSWORD:
            await interaction.response.send_message(
                "Incorrect password. Please try again.",
                ephemeral=True,
            )
            return

        await grant_premium_role(interaction)


class PremiumView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Get your Premium Role",
        style=discord.ButtonStyle.primary,
        custom_id=BUTTON_CUSTOM_ID,
    )
    async def get_premium_role(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This button only works inside a server.", ephemeral=True
            )
            return

        await interaction.response.send_modal(PremiumPasswordModal())


intents = discord.Intents.default()


async def _no_prefix(_bot: commands.Bot, _message: discord.Message) -> list[str]:
    return []


bot = commands.Bot(
    command_prefix=_no_prefix,
    intents=intents,
    help_command=None,
)


@bot.event
async def on_ready():
    bot.add_view(PremiumView())
    try:
        synced = await bot.tree.sync()
        log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
        log.info("Synced %s slash command(s)", len(synced))
    except Exception as exc:
        log.exception("Failed to sync commands: %s", exc)


@bot.tree.command(
    name="setup",
    description="Post the Premium role embed with button (admin only).",
)
@app_commands.default_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Get Premium Access",
        description=(
            "Click the button below and enter the password to receive your **Premium** role.\n\n"
            "Once you have it, you will be able to see all channels in **Premium Workflow**."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Tensor Works")

    await interaction.response.send_message(
        embed=embed,
        view=PremiumView(),
    )


async def health_handler(_request: web.Request) -> web.Response:
    return web.Response(text="Premium Role Bot is running", status=200)


async def start_health_server() -> None:
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info("Health server listening on port %s", PORT)


async def keep_render_awake() -> None:
    url = get_keep_alive_url()
    if not url:
        log.info("Keep-alive disabled (set RENDER_EXTERNAL_URL on Render or KEEP_ALIVE_URL manually)")
        return

    log.info("Keep-alive enabled, pinging %s every 14 minutes", url)
    await asyncio.sleep(30)

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    log.info("Keep-alive ping OK (%s)", resp.status)
            except Exception as exc:
                log.warning("Keep-alive ping failed: %s", exc)
            await asyncio.sleep(KEEP_ALIVE_INTERVAL)


async def run_bot() -> None:
    await start_health_server()
    asyncio.create_task(keep_render_awake())
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    if not TOKEN:
        log.error("DISCORD_TOKEN is missing.")
        log.error("On Render: add DISCORD_TOKEN under Environment in the dashboard.")
        raise SystemExit(1)

    if TOKEN == "your_bot_token_here":
        log.error("Replace the placeholder token with your real bot token.")
        raise SystemExit(1)

    log.info("Starting bot...")
    try:
        asyncio.run(run_bot())
    except discord.LoginFailure:
        log.error("Invalid bot token. Reset it in the Discord Developer Portal and update Render.")
        raise SystemExit(1) from None
    except discord.PrivilegedIntentsRequired:
        log.error(
            "Privileged intents are enabled in code but not in the Developer Portal. "
            "This bot does not need them — redeploy the latest code."
        )
        raise SystemExit(1) from None
    except Exception:
        log.exception("Bot crashed on startup")
        raise
