from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.eleve import Eleve
    from app.models.tournoi import Tournoi


class Maison(db.Model, TimestampMixin):
    __tablename__ = "maison"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    couleur: Mapped[str] = mapped_column(String(30), nullable=False)
    fondateur: Mapped[str] = mapped_column(String(100), nullable=False)
    valeurs: Mapped[Optional[str]] = mapped_column(String(255))
    reputation: Mapped[int] = mapped_column(default=0, nullable=False)

    eleves: Mapped[List["Eleve"]] = relationship(back_populates="maison")
    tournois_organises: Mapped[List["Tournoi"]] = relationship(
        back_populates="maison_organisatrice",
        foreign_keys="Tournoi.maison_organisatrice_id",
    )

    def __repr__(self) -> str:
        return f"<Maison {self.nom!r}>"
