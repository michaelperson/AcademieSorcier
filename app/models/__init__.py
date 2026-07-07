"""
Importer ce module (ou n'importe quel module qui l'importe, comme
app/__init__.py) enregistre toutes les entités sur la metadata de
db.Model — nécessaire avant tout db.create_all(), et pour que les
relationship() en chaîne de caractères ("Eleve", "Tournoi.vainqueur_id",
...) puissent se résoudre correctement au premier accès.

Un module par entité : chaque fichier ne contient qu'une classe, pour
garder les fichiers courts et les diffs Git lisibles à plusieurs sur la
semaine.
"""

from app.models.mixins import TimestampMixin

from app.models.annee_academique import AnneeAcademique
from app.models.maison import Maison
from app.models.professeur import Professeur
from app.models.cours import Cours
from app.models.eleve import Eleve
from app.models.utilisateur import Utilisateur
from app.models.inscription import Inscription
from app.models.examen import Examen
from app.models.resultat import Resultat
from app.models.competence import Competence
from app.models.maitrise import Maitrise
from app.models.tournoi import Tournoi
from app.models.duel import Duel

__all__ = [
    "TimestampMixin",
    "AnneeAcademique",
    "Maison",
    "Professeur",
    "Cours",
    "Eleve",
    "Utilisateur",
    "Inscription",
    "Examen",
    "Resultat",
    "Competence",
    "Maitrise",
    "Tournoi",
    "Duel",
]
