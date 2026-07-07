from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.eleve import Eleve
    from app.models.examen import Examen


class Resultat(db.Model, TimestampMixin):
    """Association enrichie Eleve <-> Examen : une note par élève et par
    examen. La borne exacte (ex. 0-20) se valide en jour 4 avec
    marshmallow/pydantic, pas au niveau du schéma de base.
    """

    __tablename__ = "resultat"
    __table_args__ = (
        UniqueConstraint("eleve_id", "examen_id", name="uq_resultat_eleve_examen"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    note: Mapped[float] = mapped_column(Float, nullable=False)

    eleve_id: Mapped[int] = mapped_column(ForeignKey("eleve.id"), nullable=False)
    examen_id: Mapped[int] = mapped_column(ForeignKey("examen.id"), nullable=False)

    eleve: Mapped["Eleve"] = relationship(back_populates="resultats")
    examen: Mapped["Examen"] = relationship(back_populates="resultats")

    def __repr__(self) -> str:
        return f"<Resultat eleve={self.eleve_id} examen={self.examen_id} note={self.note}>"
