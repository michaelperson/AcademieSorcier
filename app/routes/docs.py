"""
Documentation API : /openapi.json sert la spec brute, /docs l'affiche avec
Scalar (https://github.com/scalar/scalar). Pas de dépendance Python
supplémentaire : Scalar s'utilise comme un simple script à charger depuis
un CDN dans une page HTML, qui lit ensuite /openapi.json côté navigateur.
"""

from flask import Blueprint, jsonify

from app.openapi_spec import OPENAPI_SPEC

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
    return jsonify(OPENAPI_SPEC), 200


@docs_bp.get("/docs")
def documentation():
    return PAGE_SCALAR, 200, {"Content-Type": "text/html; charset=utf-8"}
