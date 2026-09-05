import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.session import async_session
from src.database.models import User, Character

class CharacterCreationModal(discord.ui.Modal, title='Nazwij swojego bohatera'):
    character_name = discord.ui.TextInput(
        label='Imię postaci',
        style=discord.TextStyle.short,
        placeholder='Wpisz imię...',
        min_length=3,
        max_length=20,
        required=True
    )

    def __init__(self, char_class: str, stats: dict[str, int]):
        super().__init__()
        self.char_class = char_class
        self.stats = stats

    async def on_submit(self, interaction: discord.Interaction):
        # Transakcyjny zapis do bazy danych
        async with async_session() as session:
            # Upsert User
            user_stmt = select(User).where(User.id == interaction.user.id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                user = User(id=interaction.user.id)
                session.add(user)
                await session.flush()
            
            # Create character
            new_char = Character(
                user_id=user.id,
                name=self.character_name.value,
                char_class=self.char_class,
                strength=self.stats["strength"],
                dexterity=self.stats["dexterity"],
                intelligence=self.stats["intelligence"],
                endurance=self.stats["endurance"],
            )
            session.add(new_char)
            await session.commit()
            
        await interaction.response.send_message(
            f"Znakomicie! Stworzono postać **{self.character_name.value}** ({self.char_class}).", 
            ephemeral=True
        )
        
        # Opcjonalnie: powiadomienie na kanale globalnym
        # Można tu poszukać kanału powitalnego z configu Gildii.
        
        # Usuwamy wątek z opóźnieniem
        if isinstance(interaction.channel, discord.Thread):
            await asyncio.sleep(10)
            try:
                await interaction.channel.delete()
            except discord.HTTPException:
                pass

class AttributeView(discord.ui.View):
    def __init__(self, char_class: str):
        super().__init__(timeout=300)
        self.char_class = char_class
        
        self.points_available = 15
        self.stats = {
            "strength": 1,
            "dexterity": 1,
            "intelligence": 1,
            "endurance": 1
        }
        self.update_buttons()

    def update_buttons(self):
        # Helper string builder
        self.desc = (
            f"**Klasa:** {self.char_class}\n"
            f"**Punkty do rozdania:** {self.points_available}\n\n"
            f"💪 Siła: {self.stats['strength']}\n"
            f"🎯 Zręczność: {self.stats['dexterity']}\n"
            f"🧠 Inteligencja: {self.stats['intelligence']}\n"
            f"🛡️ Wytrzymałość: {self.stats['endurance']}"
        )

    async def handle_stat_change(self, interaction: discord.Interaction, stat: str, amount: int):
        # Walidacja po stronie serwera
        if amount > 0 and self.points_available < amount:
            await interaction.response.send_message("Nie masz wystarczająco punktów!", ephemeral=True)
            return
            
        if amount < 0 and self.stats[stat] <= 1: # Base stat min is 1
            await interaction.response.send_message("Statystyka nie może spaść poniżej 1!", ephemeral=True)
            return

        self.points_available -= amount
        self.stats[stat] += amount
        
        self.update_buttons()
        await interaction.response.edit_message(content=self.desc, view=self)

    @discord.ui.button(label="+1 Siła", style=discord.ButtonStyle.primary, row=0)
    async def add_str(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_stat_change(interaction, "strength", 1)

    @discord.ui.button(label="-1 Siła", style=discord.ButtonStyle.secondary, row=0)
    async def sub_str(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_stat_change(interaction, "strength", -1)

    @discord.ui.button(label="+1 Zręczność", style=discord.ButtonStyle.primary, row=1)
    async def add_dex(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_stat_change(interaction, "dexterity", 1)
        
    @discord.ui.button(label="-1 Zręczność", style=discord.ButtonStyle.secondary, row=1)
    async def sub_dex(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_stat_change(interaction, "dexterity", -1)

    @discord.ui.button(label="+1 Inteligencja", style=discord.ButtonStyle.primary, row=2)
    async def add_int(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_stat_change(interaction, "intelligence", 1)

    @discord.ui.button(label="-1 Inteligencja", style=discord.ButtonStyle.secondary, row=2)
    async def sub_int(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_stat_change(interaction, "intelligence", -1)

    @discord.ui.button(label="+1 Wytrz.", style=discord.ButtonStyle.primary, row=3)
    async def add_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_stat_change(interaction, "endurance", 1)

    @discord.ui.button(label="-1 Wytrz.", style=discord.ButtonStyle.secondary, row=3)
    async def sub_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_stat_change(interaction, "endurance", -1)

    @discord.ui.button(label="Zakończ (Dalej)", style=discord.ButtonStyle.success, row=4)
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.points_available > 0:
            await interaction.response.send_message("Musisz rozdać wszystkie punkty!", ephemeral=True)
            return
            
        modal = CharacterCreationModal(self.char_class, self.stats)
        await interaction.response.send_modal(modal)


class ClassSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Wojownik', description='Walczy w zwarciu, duża siła', emoji='⚔️'),
            discord.SelectOption(label='Mag', description='Zadaje potężne obrażenia magiczne', emoji='🔮'),
            discord.SelectOption(label='Łotrzyk', description='Szybki i zabójczy z ukrycia', emoji='🗡️')
        ]
        super().__init__(placeholder='Wybierz klasę postaci...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_class = self.values[0]
        attr_view = AttributeView(selected_class)
        await interaction.response.edit_message(
            content=f"Wybrałeś: **{selected_class}**!\nTeraz rozdaj punkty atrybutów.", 
            view=attr_view
        )

class ClassSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(ClassSelect())


class OnboardingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="start", description="Rozpocznij swoją przygodę i stwórz postać")
    async def start_cmd(self, interaction: discord.Interaction):
        # Sprawdzamy czy użytkownik ma już postać (opcjonalnie z limitem postaci)
        async with async_session() as session:
            stmt = select(Character).where(Character.user_id == interaction.user.id)
            result = await session.execute(stmt)
            chars = result.scalars().all()
            
            if chars:
                await interaction.response.send_message("Masz już postać! Użyj `/profil`.", ephemeral=True)
                return

        # Tworzenie prywatnego wątku
        if isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Przygotowuję dla Ciebie miejsce...", ephemeral=True)
            
            try:
                thread = await interaction.channel.create_thread(
                    name=f"Kreator: {interaction.user.display_name}",
                    type=discord.ChannelType.private_thread,
                    invitable=False
                )
                
                await thread.add_user(interaction.user)
                
                view = ClassSelectionView()
                await thread.send(f"Witaj {interaction.user.mention}! Zacznijmy od wyboru klasy.", view=view)
            except discord.Forbidden:
                await interaction.followup.send("Bot nie ma uprawnień do tworzenia prywatnych wątków!", ephemeral=True)
        else:
            await interaction.response.send_message("Ta komenda działa tylko na kanałach tekstowych.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(OnboardingCog(bot))
