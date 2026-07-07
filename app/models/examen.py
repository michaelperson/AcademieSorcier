import datetime as dt
from typing import TYPE_CHECKING, List

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.competence import Competence
    from app.models.cours import Cours
    from app.models.resultat import Resultat


class Examen(db.Model, TimestampMixin):
    __tablename__ = "examen"

    id: Mapped[int] = mapped_column(primary_key=True)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    # Import "datetime as dt" pour éviter que l'attribut `date` ci-dessous
    # ne masque le type datetime.date dans l'annotation.
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    seuil_reussite: Mapped[float] = mapped_column(Float, nullable=False)

    cours_id: Mapped[int] = mapped_column(ForeignKey("cours.id"), nullable=False)

    cours: Mapped["Cours"] = relationship(back_populates="examens")
    resultats: Mapped[List["Resultat"]] = relationship(back_populates="examen")
    competences_conditionnees: Mapped[List["Competence"]] = relationship(
        back_populates="examen_condition"
    )

    def __repr__(self) -> str:
        return f"<Examen {self.titre!r}>"
