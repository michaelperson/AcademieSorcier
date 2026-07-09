from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.dal.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.dal.models.annee_academique import AnneeAcademique
    from app.dal.models.examen import Examen
    from app.dal.models.inscription import Inscription
    from app.dal.models.professeur import Professeur


class Cours(db.Model, TimestampMixin):
    __tablename__ = "cours"

    id: Mapped[int] = mapped_column(primary_key=True)
    intitule: Mapped[str] = mapped_column(String(150), nullable=False)
    niveau_requis: Mapped[int] = mapped_column(nullable=False)
    capacite_max: Mapped[int] = mapped_column(nullable=False)

    professeur_id: Mapped[int] = mapped_column(ForeignKey("professeur.id"), nullable=False)
    annee_academique_id: Mapped[int] = mapped_column(
        ForeignKey("annee_academique.id"), nullable=False
    )

    professeur: Mapped["Professeur"] = relationship(back_populates="cours")
    annee_academique: Mapped["AnneeAcademique"] = relationship(back_populates="cours")

    # Pas de cascade delete définie ici volontairement : décidez consciemment
    # si supprimer un cours doit entraîner celle de ses examens/inscriptions,
    # ou si ça doit être refusé tant qu'il en reste (plus sûr par défaut).
    examens: Mapped[List["Examen"]] = relationship(back_populates="cours")
    inscriptions: Mapped[List["Inscription"]] = relationship(back_populates="cours")

    def __repr__(self) -> str:
        return f"<Cours {self.intitule!r}>"
