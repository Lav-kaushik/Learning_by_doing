from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
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

    # add relative access -> url_mapping.analytics
    analytics: Mapped["URLAnalytics | None"] = relationship(
        back_populates="url_mapping"
    )
class URLAnalytics(Base):

    __tablename__ = "url_analytics"

    short_url: Mapped[str] =  mapped_column(
            ForeignKey("url_mappings.shortened_url"),
            primary_key=True
        )
    click_count: Mapped[int] = mapped_column(default=0)
    last_accessed: Mapped[datetime] = mapped_column(server_default=func.now(), server_onupdate=func.now())

    # add relative access -> url_analytics.url_mapping
    url_mapping: Mapped["URLMapping"] = relationship(
        back_populates="analytics"
    )
