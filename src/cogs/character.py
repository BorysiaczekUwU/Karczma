import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database.session import async_session
from src.database.models import Character, Inventory
from src.services.character_svc import CharacterService

class CharacterCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profil", description="Wyświetla profil Twojej postaci")
    async def profile_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with async_session() as session:
            # We use selectinload to eagerly load the inventory and related items
            stmt = select(Character).where(Character.user_id == interaction.user.id).options(
                selectinload(Character.inventory).selectinload(Inventory.item)
            )
            result = await session.execute(stmt)
            character = result.scalar_one_or_none()

            if not character:
                await interaction.followup.send("Nie masz jeszcze postaci! Użyj `/start`.")
                return

            # Compute stats
            equipped = [inv for inv in character.inventory if inv.is_equipped]
            max_hp = CharacterService.get_max_hp(character)
            armor = CharacterService.get_armor(character, equipped)
            damage = CharacterService.get_damage(character, equipped)
            
            # Simple XP curve for example
            next_level_xp = character.level * 100
            xp_bar = CharacterService.generate_xp_bar(character.xp, next_level_xp)

            # Build Embed
            embed = discord.Embed(
                title=f"Profil: {character.name}",
                description=f"**Klasa:** {character.char_class} | **Poziom:** {character.level}",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            embed.add_field(name="Doświadczenie", value=xp_bar, inline=False)
            embed.add_field(name="Złoto", value=f"🪙 {character.gold}", inline=False)

            stats_text = (
                f"❤️ **Max HP:** {max_hp}\n"
                f"🛡️ **Pancerz:** {armor:.1f}\n"
                f"⚔️ **Obrażenia:** {damage:.1f}"
            )
            embed.add_field(name="Statystyki Bojowe", value=stats_text, inline=True)

            attrs_text = (
                f"💪 Siła: {character.strength}\n"
                f"🎯 Zręczność: {character.dexterity}\n"
                f"🧠 Inteligencja: {character.intelligence}\n"
                f"🛡️ Wytrz.: {character.endurance}"
            )
            embed.add_field(name="Atrybuty", value=attrs_text, inline=True)
            
            # Ekwipunek
            eq_text = ""
            if not equipped:
                eq_text = "*Brak wyekwipowanych przedmiotów*"
            else:
                for inv in equipped:
                    eq_text += f"- {inv.item.name} ({inv.item.item_type.name})\n"
            
            embed.add_field(name="Wyposażenie", value=eq_text, inline=False)

            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(CharacterCog(bot))
