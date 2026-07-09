"""
Documentation API : /openapi.json sert la spec brute, /docs l'affiche avec
Scalar (https://github.com/scalar/scalar). Pas de dépendance Python
supplémentaire pour l'affichage : Scalar s'utilise comme un simple script
à charger depuis un CDN dans une page HTML, qui lit ensuite /openapi.json
côté navigateur.

La spec elle-même est construite une fois au démarrage à partir des
docstrings des routes (voir app/openapi_generator.py et create_app dans
app/__init__.py) et mise en cache sur current_app.config["OPENAPI_SPEC"] —
ces deux vues n'ont plus qu'à la relire, elles ne la construisent pas.
"""

from flask import Blueprint, current_app, jsonify

docs_bp = Blueprint("docs", __name__)

PAGE_SCALAR = """<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <title>Académie de Sorcellerie — Documentation API</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <script id="api-reference" data-url="/openapi.json"></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>
"""


@docs_bp.get("/openapi.json")
def openapi_json():
    return jsonify(current_app.config["OPENAPI_SPEC"]), 200


@docs_bp.get("/docs")
def documentation():
    return PAGE_SCALAR, 200, {"Content-Type": "text/html; charset=utf-8"}
