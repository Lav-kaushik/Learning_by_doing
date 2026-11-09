from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class URLMapping(Base):
    
    __tablename__ = "url_mappings"

    original_url: Mapped[str] = mapped_column(unique=True)
    shortened_url: Mapped[str] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


