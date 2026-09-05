import asyncio
import logging
import discord
from discord.ext import commands

from src.config import settings
from src.database.session import engine
from src.database.models import Base

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("karczma_bot")

class KarczmaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        logger.info("Inicjalizacja bazy danych (w środowisku dev)...")
        # In production, use alembic migrations instead of create_all
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Ładowanie modułów (cogs)...")
        initial_extensions = [
            "src.cogs.onboarding",
            "src.cogs.character",
            "src.cogs.economy",
            "src.cogs.combat",
            # "src.cogs.rp_engine" # TODO
        ]
        
        for ext in initial_extensions:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded extension {ext}")
            except Exception as e:
                logger.error(f"Failed to load extension {ext}: {e}")

        if settings.sync_commands:
            logger.info("Synchronizacja komend slash (Application Commands)...")
            if settings.guild_id:
                guild = discord.Object(id=settings.guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Synchronizacja dla gildii {settings.guild_id} zakończona.")
            else:
                await self.tree.sync()
                logger.info("Synchronizacja globalna zakończona.")

    async def on_ready(self):
        logger.info(f"Zalogowano jako {self.user} (ID: {self.user.id})")
        await self.change_presence(activity=discord.Game(name="RPG Karczma"))

def main():
    bot = KarczmaBot()
    token = settings.bot_token.get_secret_value()
    bot.run(token, log_handler=None)

if __name__ == "__main__":
    main()
