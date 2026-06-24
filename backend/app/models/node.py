from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(255))
    node_type: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
