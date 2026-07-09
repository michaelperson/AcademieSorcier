from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.dal.models.enums import StatutResultat
from app.dal.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.dal.models.eleve import Eleve
    from app.dal.models.examen import Examen


class Resultat(db.Model, TimestampMixin):
    """Association enrichie Eleve <-> Examen : une note par élève et par
    examen. La borne exacte (ex. 0-20) se valide en jour 4 avec
    marshmallow/pydantic, pas au niveau du schéma de base.

    `statut` (réussi/échec à CET examen) reste nul tant que l'examen n'a
    pas été clôturé (POST /examens/<id>/cloture) : une note seule ne dit
    pas encore si elle est suffisante, il faut la décision de clôture pour
    ça. Ne pas confondre avec Inscription.statut, qui parle du cours dans
    son ensemble et se met à jour séparément (POST /cours/<id>/cloture).
    """

    __tablename__ = "resultat"
    __table_args__ = (
        UniqueConstraint("eleve_id", "examen_id", name="uq_resultat_eleve_examen"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    note: Mapped[float] = mapped_column(Float, nullable=False)
    statut: Mapped[Optional[StatutResultat]] = mapped_column(
        SQLEnum(StatutResultat, values_callable=lambda enum_cls: [m.value for m in enum_cls]),
        nullable=True,
        default=None,
    )

    eleve_id: Mapped[int] = mapped_column(ForeignKey("eleve.id"), nullable=False)
    examen_id: Mapped[int] = mapped_column(ForeignKey("examen.id"), nullable=False)

    eleve: Mapped["Eleve"] = relationship(back_populates="resultats")
    examen: Mapped["Examen"] = relationship(back_populates="resultats")

    def __repr__(self) -> str:
        return f"<Resultat eleve={self.eleve_id} examen={self.examen_id} note={self.note}>"
