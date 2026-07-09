from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.dal.models.enums import RoleUtilisateur
from app.dal.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.dal.models.eleve import Eleve
    from app.dal.models.professeur import Professeur


class Utilisateur(db.Model, TimestampMixin):
    """Le lien vers Eleve ou Professeur selon le rôle est une contrainte
    applicative (cahier des charges, jour 1) : rien ici n'empêche en base
    de remplir les deux colonnes ou aucune des deux. À vérifier dans la
    couche service/validation avant toute insertion.
    """

    __tablename__ = "utilisateur"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    # En clair pour l'instant, comme demandé par le cahier des charges au jour 1.
    # TODO sécurité : à hacher avant toute mise en situation réelle.
    mot_de_passe: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleUtilisateur] = mapped_column(
        SQLEnum(RoleUtilisateur, values_callable=lambda enum_cls: [m.value for m in enum_cls]),
        nullable=False,
    )

    eleve_id: Mapped[Optional[int]] = mapped_column(ForeignKey("eleve.id"))
    professeur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("professeur.id"))

    eleve: Mapped[Optional["Eleve"]] = relationship(back_populates="utilisateur")
    professeur: Mapped[Optional["Professeur"]] = relationship(back_populates="utilisateur")

    def __repr__(self) -> str:
        return f"<Utilisateur {self.email!r} ({self.role.value})>"
