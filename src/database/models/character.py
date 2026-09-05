from sqlalchemy import BigInteger, ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .inventory import Inventory

class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    char_class: Mapped[str] = mapped_column(String(30), nullable=False) # e.g. Wojownik, Mag, Łotrzyk
    
    # Currency
    gold: Mapped[int] = mapped_column(Integer, default=0)
    
    # Stats
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    
    strength: Mapped[int] = mapped_column(Integer, default=1)
    dexterity: Mapped[int] = mapped_column(Integer, default=1)
    intelligence: Mapped[int] = mapped_column(Integer, default=1)
    endurance: Mapped[int] = mapped_column(Integer, default=1)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="characters")
    inventory: Mapped[List["Inventory"]] = relationship(
        "Inventory", back_populates="character", cascade="all, delete-orphan"
    )
