from sqlalchemy import String, Integer, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
import enum
from .base import Base

if TYPE_CHECKING:
    from .inventory import Inventory

class ItemType(str, enum.Enum):
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    CONSUMABLE = "CONSUMABLE"
    MATERIAL = "MATERIAL"

class Item(Base):
    """Słownik/szablon przedmiotów dostępnych w grze."""
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    
    item_type: Mapped[ItemType] = mapped_column(Enum(ItemType), nullable=False)
    
    # E.g. base damage for weapons, defense for armor, heal amount for consumables
    power: Mapped[int] = mapped_column(Integer, default=0) 
    
    max_stack: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[int] = mapped_column(Integer, default=0)
    
    is_tradable: Mapped[bool] = mapped_column(Boolean, default=True)

    inventories: Mapped[List["Inventory"]] = relationship("Inventory", back_populates="item")
