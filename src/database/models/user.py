from sqlalchemy import BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from .base import Base

if TYPE_CHECKING:
    from .character import Character

class User(Base):
    __tablename__ = "users"

    # Discord user ID is a very large integer, so BigInteger is used
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    characters: Mapped[List["Character"]] = relationship(
        "Character", back_populates="user", cascade="all, delete-orphan"
    )
