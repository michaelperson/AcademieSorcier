from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.dal.models.enums import StatutInscription
from app.dal.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.dal.models.cours import Cours
    from app.dal.models.eleve import Eleve


class Inscription(db.Model, TimestampMixin):
    """Association enrichie Eleve <-> Cours. La contrainte unique empêche
    une double inscription au même cours ; la vérification de la capacité
    maximale du cours reste une règle applicative (jour 2), pas une
    contrainte de schéma — la base ne connaît pas `capacite_max` au moment
    de l'insertion.
    """

    __tablename__ = "inscription"
    __table_args__ = (
        UniqueConstraint("eleve_id", "cours_id", name="uq_inscription_eleve_cours"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date_inscription: Mapped[date] = mapped_column(Date, nullable=False)
    statut: Mapped[StatutInscription] = mapped_column(
        SQLEnum(StatutInscription, values_callable=lambda enum_cls: [m.value for m in enum_cls]),
        default=StatutInscription.INSCRIT,
        nullable=False,
    )

    eleve_id: Mapped[int] = mapped_column(ForeignKey("eleve.id"), nullable=False)
    cours_id: Mapped[int] = mapped_column(ForeignKey("cours.id"), nullable=False)

    eleve: Mapped["Eleve"] = relationship(back_populates="inscriptions")
    cours: Mapped["Cours"] = relationship(back_populates="inscriptions")

    def __repr__(self) -> str:
        return f"<Inscription eleve={self.eleve_id} cours={self.cours_id}>"
