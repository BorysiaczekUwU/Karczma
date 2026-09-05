from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Guild(Base):
    """Konfiguracja dla danego serwera Discord (gildii)."""
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    prefix: Mapped[str] = mapped_column(String(10), default="!")
    welcome_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    log_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
