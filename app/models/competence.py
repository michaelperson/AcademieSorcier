from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.enums import SourceDeblocage
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.examen import Examen
    from app.models.maitrise import Maitrise


class Competence(db.Model, TimestampMixin):
    __tablename__ = "competence"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    categorie: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    condition_type: Mapped[SourceDeblocage] = mapped_column(
        SQLEnum(SourceDeblocage, values_callable=lambda enum_cls: [m.value for m in enum_cls]),
        nullable=False,
    )

    # Remplis uniquement si condition_type == SourceDeblocage.EXAMEN.
    examen_id: Mapped[Optional[int]] = mapped_column(ForeignKey("examen.id"))
    note_min: Mapped[Optional[float]] = mapped_column(Float)

    examen_condition: Mapped[Optional["Examen"]] = relationship(
        back_populates="competences_conditionnees"
    )
    maitrises: Mapped[List["Maitrise"]] = relationship(back_populates="competence")

    def __repr__(self) -> str:
        return f"<Competence {self.nom!r}>"
