import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database.session import async_session
from src.database.models import Character, Inventory
from src.services.character_svc import CharacterService
from src.services.combat_svc import CombatEngine, CombatEntity


class CombatView(discord.ui.View):
    def __init__(self, author_id: int, engine: CombatEngine):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.engine = engine

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("To nie Twoja walka!", ephemeral=True)
            return False
        return True

    async def update_state(self, interaction: discord.Interaction):
        if self.engine.is_finished:
            # Wyłączenie przycisków
            for child in self.children:
                child.disabled = True
            self.stop()
            
        embed = self.engine.get_status_embed(discord.Embed)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Atak", style=discord.ButtonStyle.danger, row=0, emoji="⚔️")
    async def attack_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.engine.process_player_action("attack")
        await self.update_state(interaction)

    @discord.ui.button(label="Mikstura", style=discord.ButtonStyle.success, row=0, emoji="🧪")
    async def potion_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.engine.process_player_action("potion")
        await self.update_state(interaction)

    @discord.ui.button(label="Ucieczka", style=discord.ButtonStyle.secondary, row=1, emoji="🏃")
    async def flee_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.engine.process_player_action("flee")
        await self.update_state(interaction)

    async def on_timeout(self) -> None:
        if not self.engine.is_finished:
            self.engine.is_finished = True
            self.engine.log.append("⏰ Walka przerwana z powodu nieaktywności!")
            # Trzeba by było zaktualizować wiadomość, ale on_timeout nie ma obiektu interaction.
            # Zwykle trzymamy referencję do message i ją edytujemy.


class CombatCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="hunt", description="Wyrusz na polowanie na potwory")
    async def hunt_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with async_session() as session:
            stmt = select(Character).where(Character.user_id == interaction.user.id).options(
                selectinload(Character.inventory).selectinload(Inventory.item)
            )
            result = await session.execute(stmt)
            character = result.scalar_one_or_none()

            if not character:
                await interaction.followup.send("Nie masz jeszcze postaci! Użyj `/start`.")
                return
                
            equipped = [inv for inv in character.inventory if inv.is_equipped]
            player_hp = CharacterService.get_max_hp(character)
            
            player_entity = CombatEntity(
                name=character.name,
                hp=player_hp,
                max_hp=player_hp,
                damage=CharacterService.get_damage(character, equipped),
                armor=CharacterService.get_armor(character, equipped),
                is_player=True
            )
            
            # Simple scaling enemy based on player level
            enemy_entity = CombatEntity(
                name=f"Goblin Poziom {character.level}",
                hp=50 + (character.level * 10),
                max_hp=50 + (character.level * 10),
                damage=5 + (character.level * 2),
                armor=character.level,
                is_player=False
            )
            
            engine = CombatEngine(player_entity, enemy_entity)
            view = CombatView(interaction.user.id, engine)
            
            embed = engine.get_status_embed(discord.Embed)
            msg = await interaction.followup.send(embed=embed, view=view, wait=True)
            view.message = msg # store reference for timeout edits if needed

async def setup(bot: commands.Bot):
    await bot.add_cog(CombatCog(bot))
