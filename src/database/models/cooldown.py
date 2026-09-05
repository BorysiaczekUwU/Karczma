from sqlalchemy import BigInteger, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
import datetime
from .base import Base

class Cooldown(Base):
    """Przechowywanie długoterminowych cooldownów (np. komenda daily)."""
    __tablename__ = "cooldowns"

    # We use composite logic or just string key for flexibility, but let's make it user + command
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    command_name: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
