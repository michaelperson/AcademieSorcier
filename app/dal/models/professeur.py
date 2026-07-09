from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.dal.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.dal.models.cours import Cours
    from app.dal.models.utilisateur import Utilisateur


class Professeur(db.Model, TimestampMixin):
    __tablename__ = "professeur"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    matiere_enseignee: Mapped[str] = mapped_column(String(100), nullable=False)
    anciennete: Mapped[int] = mapped_column(nullable=False)

    cours: Mapped[List["Cours"]] = relationship(back_populates="professeur")
    utilisateur: Mapped[Optional["Utilisateur"]] = relationship(back_populates="professeur")

    def __repr__(self) -> str:
        return f"<Professeur {self.nom!r}>"
