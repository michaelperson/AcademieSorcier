from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.cours import Cours


class AnneeAcademique(db.Model, TimestampMixin):
    """Une année scolaire (ex. "2025-2026"). Centralise le seuil de
    promotion et la marque de clôture utilisés par l'endpoint de passage
    de fin d'année (jour 4) : `cloturee_le` rempli = un second rejeu de la
    clôture doit être refusé explicitement.

    Alternative plus simple, si vous préférez : garder l'année comme un
    simple champ texte sur Cours et gérer la garde de clôture ailleurs.
    Cette table n'est pas imposée par le cahier des charges.
    """

    __tablename__ = "annee_academique"

    id: Mapped[int] = mapped_column(primary_key=True)
    libelle: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    seuil_promotion: Mapped[float] = mapped_column(Float, nullable=False)
    cloturee_le: Mapped[Optional[datetime]] = mapped_column(DateTime)

    cours: Mapped[List["Cours"]] = relationship(back_populates="annee_academique")

    def __repr__(self) -> str:
        return f"<AnneeAcademique {self.libelle!r}>"
