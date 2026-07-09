from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.dal.models.enums import StatutEleve
from app.dal.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.dal.models.inscription import Inscription
    from app.dal.models.maison import Maison
    from app.dal.models.maitrise import Maitrise
    from app.dal.models.resultat import Resultat
    from app.dal.models.tournoi import Tournoi
    from app.dal.models.utilisateur import Utilisateur


class Eleve(db.Model, TimestampMixin):
    __tablename__ = "eleve"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    annee_etude: Mapped[int] = mapped_column(nullable=False)  # 1 à 7 — borne à valider jour 4
    familier: Mapped[Optional[str]] = mapped_column(String(100))
    statut: Mapped[StatutEleve] = mapped_column(
        SQLEnum(StatutEleve, values_callable=lambda enum_cls: [m.value for m in enum_cls]),
        default=StatutEleve.ACTIF,
        nullable=False,
    )

    maison_id: Mapped[int] = mapped_column(ForeignKey("maison.id"), nullable=False)

    maison: Mapped["Maison"] = relationship(back_populates="eleves")
    utilisateur: Mapped[Optional["Utilisateur"]] = relationship(back_populates="eleve")
    inscriptions: Mapped[List["Inscription"]] = relationship(back_populates="eleve")
    resultats: Mapped[List["Resultat"]] = relationship(back_populates="eleve")
    maitrises: Mapped[List["Maitrise"]] = relationship(back_populates="eleve")
    tournois_remportes: Mapped[List["Tournoi"]] = relationship(
        back_populates="vainqueur", foreign_keys="Tournoi.vainqueur_eleve_id"
    )

    def __repr__(self) -> str:
        return f"<Eleve {self.nom!r}>"
