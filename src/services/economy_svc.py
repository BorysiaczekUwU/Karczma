from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models import Character, Inventory, Item

class InsufficientFundsError(Exception):
    pass

class InsufficientItemsError(Exception):
    pass

class EconomyService:
    @staticmethod
    async def transfer_gold(session: AsyncSession, from_char_id: int, to_char_id: int, amount: int) -> bool:
        """Bezpieczny transfer waluty między graczami przy użyciu blokad FOR UPDATE."""
        if amount <= 0:
            raise ValueError("Kwota transferu musi być większa od 0.")

        # Zawsze sortujemy ID, by uniknąć deadlocków (np. gdy A -> B i B -> A w tej samej chwili)
        first_id, second_id = sorted([from_char_id, to_char_id])
        
        stmt = select(Character).where(Character.id.in_([first_id, second_id])).with_for_update()
        result = await session.execute(stmt)
        characters = {c.id: c for c in result.scalars().all()}
        
        sender = characters.get(from_char_id)
        receiver = characters.get(to_char_id)
        
        if not sender or not receiver:
            raise ValueError("Nie znaleziono jednego z graczy.")
            
        if sender.gold < amount:
            raise InsufficientFundsError("Niewystarczająca ilość złota.")
            
        sender.gold -= amount
        receiver.gold += amount
        
        return True

    @staticmethod
    async def buy_item_from_shop(session: AsyncSession, char_id: int, item_id: int, quantity: int = 1) -> bool:
        """Kupno przedmiotu ze sklepu systemowego (NPC)."""
        if quantity <= 0:
            raise ValueError("Ilość musi być większa od 0.")
            
        # Lock character record
        char_stmt = select(Character).where(Character.id == char_id).with_for_update()
        char_result = await session.execute(char_stmt)
        character = char_result.scalar_one_or_none()
        
        if not character:
            raise ValueError("Postać nie istnieje.")
            
        # Fetch item info (no need to lock the shop item template)
        item_stmt = select(Item).where(Item.id == item_id)
        item_result = await session.execute(item_stmt)
        item = item_result.scalar_one_or_none()
        
        if not item:
            raise ValueError("Przedmiot nie istnieje.")
            
        total_cost = item.price * quantity
        if character.gold < total_cost:
            raise InsufficientFundsError("Niewystarczająca ilość złota.")
            
        character.gold -= total_cost
        
        # Add to inventory (upsert pattern logic)
        inv_stmt = select(Inventory).where(
            Inventory.character_id == char_id, 
            Inventory.item_id == item_id
        ).with_for_update()
        inv_result = await session.execute(inv_stmt)
        inventory_record = inv_result.scalar_one_or_none()
        
        if inventory_record and item.max_stack > 1:
            # We can stack
            inventory_record.quantity += quantity
        else:
            # Create new stack or instance (weapons typically don't stack)
            for _ in range(quantity if item.max_stack == 1 else 1):
                new_inv = Inventory(
                    character_id=char_id,
                    item_id=item_id,
                    quantity=1 if item.max_stack == 1 else quantity
                )
                session.add(new_inv)
                
        return True
