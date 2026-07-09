from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """À combiner avec db.Model sur toute entité qui doit garder une trace
    de sa création et de sa dernière modification (exigé par le cahier des
    charges au jour 4, mais autant le poser dès le jour 1 plutôt que de
    retoucher chaque modèle plus tard).

    Usage :
        class Maison(db.Model, TimestampMixin):
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
