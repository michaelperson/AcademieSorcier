from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import SourceDeblocage
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.competence import Competence
    from app.models.eleve import Eleve
    from app.models.examen import Examen
    from app.models.tournoi import Tournoi


class Maitrise(db.Model, TimestampMixin):
    """Association enrichie Eleve <-> Competence : le déblocage effectif.
    La contrainte unique (eleve_id, competence_id) est ce qui garantit
    l'idempotence demandée au jour 3 : relancer l'évaluation des
    compétences débloquées après une clôture d'examen ne doit jamais créer
    de doublon.

    source_examen_id et source_tournoi_id sont deux colonnes nullables
    plutôt qu'une seule colonne générique (source_type + source_id sans
    contrainte de clé étrangère) : ça coûte une colonne de plus, mais ça
    reste vérifiable par la base plutôt que de reposer uniquement sur le
    code applicatif.
    """

    __tablename__ = "maitrise"
    __table_args__ = (
        UniqueConstraint("eleve_id", "competence_id", name="uq_maitrise_eleve_competence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date_obtention: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[SourceDeblocage] = mapped_column(
        SQLEnum(SourceDeblocage, values_callable=lambda enum_cls: [m.value for m in enum_cls]),
        nullable=False,
    )

    eleve_id: Mapped[int] = mapped_column(ForeignKey("eleve.id"), nullable=False)
    competence_id: Mapped[int] = mapped_column(ForeignKey("competence.id"), nullable=False)
    source_examen_id: Mapped[Optional[int]] = mapped_column(ForeignKey("examen.id"))
    source_tournoi_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tournoi.id"))

    eleve: Mapped["Eleve"] = relationship(back_populates="maitrises")
    competence: Mapped["Competence"] = relationship(back_populates="maitrises")
    source_examen: Mapped[Optional["Examen"]] = relationship(foreign_keys=[source_examen_id])
    source_tournoi: Mapped[Optional["Tournoi"]] = relationship(foreign_keys=[source_tournoi_id])

    def __repr__(self) -> str:
        return f"<Maitrise eleve={self.eleve_id} competence={self.competence_id}>"
