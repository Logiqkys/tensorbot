import asyncio
import logging
import os
import sys

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
PREMIUM_ROLE_NAME = "Premium"
BUTTON_CUSTOM_ID = "premium_role_button"
PORT = int(os.getenv("PORT", "10000"))


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
            await member.add_roles(premium_role, reason="Premium role button clicked")
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
            "Click the button below to receive your **Premium** role.\n\n"
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


async def run_bot() -> None:
    await start_health_server()
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
