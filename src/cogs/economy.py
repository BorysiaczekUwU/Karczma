import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select

from src.database.session import async_session
from src.database.models import Character
from src.services.economy_svc import EconomyService, InsufficientFundsError

class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pay", description="Przelej złoto innej postaci")
    async def pay_cmd(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Kwota musi być większa od zera!", ephemeral=True)
            return

        if target.id == interaction.user.id:
            await interaction.response.send_message("Nie możesz przelać złota samemu sobie!", ephemeral=True)
            return

        await interaction.response.defer()

        async with async_session() as session:
            # Check characters exist
            stmt = select(Character).where(Character.user_id.in_([interaction.user.id, target.id]))
            result = await session.execute(stmt)
            chars = {c.user_id: c for c in result.scalars().all()}
            
            sender_char = chars.get(interaction.user.id)
            receiver_char = chars.get(target.id)

            if not sender_char:
                await interaction.followup.send("Nie masz postaci!")
                return
            if not receiver_char:
                await interaction.followup.send("Cel nie ma postaci!")
                return

            try:
                # Perform atomic transfer
                await EconomyService.transfer_gold(
                    session=session, 
                    from_char_id=sender_char.id, 
                    to_char_id=receiver_char.id, 
                    amount=amount
                )
                await session.commit()
                await interaction.followup.send(f"💸 Przelałeś {amount} złota do {target.mention}!")
            except InsufficientFundsError:
                await session.rollback()
                await interaction.followup.send("❌ Nie masz wystarczająco złota.")
            except Exception as e:
                await session.rollback()
                await interaction.followup.send("❌ Wystąpił błąd podczas transakcji.")

async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
