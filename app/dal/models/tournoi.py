from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.dal.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.dal.models.duel import Duel
    from app.dal.models.eleve import Eleve
    from app.dal.models.maison import Maison


class Tournoi(db.Model, TimestampMixin):
    __tablename__ = "tournoi"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    annee: Mapped[int] = mapped_column(nullable=False)
    # Même logique de garde anti-rejeu que AnneeAcademique.cloturee_le.
    cloture_le: Mapped[Optional[datetime]] = mapped_column(DateTime)

    maison_organisatrice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("maison.id"))
    vainqueur_eleve_id: Mapped[Optional[int]] = mapped_column(ForeignKey("eleve.id"))

    maison_organisatrice: Mapped[Optional["Maison"]] = relationship(
        back_populates="tournois_organises", foreign_keys=[maison_organisatrice_id]
    )
    vainqueur: Mapped[Optional["Eleve"]] = relationship(
        back_populates="tournois_remportes", foreign_keys=[vainqueur_eleve_id]
    )
    duels: Mapped[List["Duel"]] = relationship(back_populates="tournoi")

    def __repr__(self) -> str:
        return f"<Tournoi {self.nom!r}>"
