from src.database.models import Character, Inventory
from typing import List

class CharacterService:
    @staticmethod
    def get_max_hp(character: Character) -> int:
        """Max HP = Wytrzymałość * 10 + Poziom * 5"""
        return character.endurance * 10 + character.level * 5

    @staticmethod
    def get_armor(character: Character, equipped_items: List[Inventory]) -> float:
        """Pancerz = Zręczność * 0.5 + bonus z ekwipunku"""
        base_armor = character.dexterity * 0.5
        
        # Calculate bonus from equipped items
        equipment_bonus = sum(
            inv.item.power for inv in equipped_items 
            if inv.is_equipped and inv.item.item_type.name == "ARMOR"
        )
        
        return base_armor + equipment_bonus

    @staticmethod
    def get_damage(character: Character, equipped_items: List[Inventory]) -> float:
        """Obrażenia = Siła (dla Wojownika) lub Inteligencja (dla Maga) * 1.5 + broń"""
        if character.char_class.lower() == "mag":
            base_dmg = character.intelligence * 1.5
        else:
            # Wojownik, Łotrzyk, etc.
            base_dmg = character.strength * 1.5
            
        # Calculate bonus from equipped weapons
        equipment_bonus = sum(
            inv.item.power for inv in equipped_items 
            if inv.is_equipped and inv.item.item_type.name == "WEAPON"
        )
        
        return base_dmg + equipment_bonus
    
    @staticmethod
    def generate_xp_bar(current_xp: int, next_level_xp: int, length: int = 10) -> str:
        """Generuje pasek postępu XP ze znaków ASCII."""
        progress = min(current_xp / next_level_xp, 1.0)
        filled_length = int(length * progress)
        bar = '█' * filled_length + '░' * (length - filled_length)
        return f"[{bar}] {current_xp}/{next_level_xp}"
