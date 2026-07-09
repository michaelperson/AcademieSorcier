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

from app.dal.models.mixins import TimestampMixin

from app.dal.models.annee_academique import AnneeAcademique
from app.dal.models.maison import Maison
from app.dal.models.professeur import Professeur
from app.dal.models.cours import Cours
from app.dal.models.eleve import Eleve
from app.dal.models.utilisateur import Utilisateur
from app.dal.models.inscription import Inscription
from app.dal.models.examen import Examen
from app.dal.models.resultat import Resultat
from app.dal.models.competence import Competence
from app.dal.models.maitrise import Maitrise
from app.dal.models.tournoi import Tournoi
from app.dal.models.duel import Duel

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
