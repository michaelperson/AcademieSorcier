from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.dal.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.dal.models.eleve import Eleve
    from app.dal.models.tournoi import Tournoi


class Duel(db.Model, TimestampMixin):
    """Trois colonnes pointent vers Eleve (eleve_1, eleve_2, vainqueur), ce
    qui impose de préciser `foreign_keys` sur chacune : sans ça, SQLAlchemy
    ne peut pas deviner quelle colonne utiliser pour chaque relation.

    Volontairement, pas de collection inverse sur Eleve (duels_joues,
    duels_gagnes...) : ça éviterait de multiplier les relations à sens
    unique sur ce modèle pour un bénéfice limité. Pour "mes duels",
    interrogez Duel directement, par exemple :

        from sqlalchemy import or_
        Duel.query.filter(
            or_(Duel.eleve_1_id == eleve_id, Duel.eleve_2_id == eleve_id)
        )
    """

    __tablename__ = "duel"

    id: Mapped[int] = mapped_column(primary_key=True)

    tournoi_id: Mapped[int] = mapped_column(ForeignKey("tournoi.id"), nullable=False)
    eleve_1_id: Mapped[int] = mapped_column(ForeignKey("eleve.id"), nullable=False)
    eleve_2_id: Mapped[int] = mapped_column(ForeignKey("eleve.id"), nullable=False)
    vainqueur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("eleve.id"))

    tournoi: Mapped["Tournoi"] = relationship(back_populates="duels")
    eleve_1: Mapped["Eleve"] = relationship(foreign_keys=[eleve_1_id])
    eleve_2: Mapped["Eleve"] = relationship(foreign_keys=[eleve_2_id])
    vainqueur: Mapped[Optional["Eleve"]] = relationship(foreign_keys=[vainqueur_id])

    def __repr__(self) -> str:
        return f"<Duel {self.eleve_1_id} vs {self.eleve_2_id}>"
