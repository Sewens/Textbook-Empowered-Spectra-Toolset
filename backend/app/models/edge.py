from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Edge(Base):
    __tablename__ = "edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_external_id: Mapped[str] = mapped_column(String(128), index=True)
    target_external_id: Mapped[str] = mapped_column(String(128), index=True)
    edge_type: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
