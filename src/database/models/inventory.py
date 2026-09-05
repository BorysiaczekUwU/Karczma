from sqlalchemy import ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from .base import Base

if TYPE_CHECKING:
    from .character import Character
    from .item import Item

class Inventory(Base):
    """Konkretna instancja przedmiotu w ekwipunku gracza."""
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id", ondelete="RESTRICT"), index=True)
    
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Specific stats for this instance (e.g., durability)
    durability: Mapped[int | None] = mapped_column(Integer, nullable=True)

    character: Mapped["Character"] = relationship("Character", back_populates="inventory")
    item: Mapped["Item"] = relationship("Item", back_populates="inventories")
