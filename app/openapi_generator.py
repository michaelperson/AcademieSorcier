"""
Génère la spec OpenAPI en observant l'application plutôt qu'en la
recopiant à la main : chaque vue documente sa propre opération dans un
bloc YAML placé dans sa docstring, juste après un séparateur `---`
(convention apispec, https://apispec.readthedocs.io/). Ce module se
contente de parcourir app.url_map et de les rassembler.

Ce qui a changé par rapport à l'ancien app/openapi_spec.py (jours 1 à 4,
un dict PATHS tenu à la main) : une route qu'on ajoute ou qu'on modifie
documente désormais son propre comportement au même endroit que son code,
il n'y a plus de fichier séparé à se souvenir de garder synchronisé. Une
vue sans bloc YAML dans sa docstring n'apparaît simplement pas dans la
spec — c'est le cas de /openapi.json et /docs elles-mêmes (voir
app/routes/docs.py), documenter la documentation n'aurait rien apporté.

Les schémas de composants (forme des ressources, erreurs, sécurité) restent
centralisés dans app/openapi_components.py : ce sont eux qui sont
réutilisés par $ref depuis plusieurs docstrings, contrairement au résumé
ou aux réponses d'une opération, qui n'appartiennent qu'à elle.
"""

from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin

from app.openapi_components import COMPONENTS_SCHEMAS, INFO, SECURITY_SCHEMES, SERVERS, TAGS


def construire_spec(app):
    """Construit la spec OpenAPI de `app` en observant ses routes.

    Appelée une fois au démarrage (voir create_app) plutôt qu'à chaque
    requête sur /openapi.json : introspecter ~35 endpoints est bon marché,
    mais le faire à chaque appel n'apporterait rien puisque les docstrings
    ne changent pas en cours d'exécution, seulement au redémarrage.
    """
    spec = APISpec(
        title=INFO["title"],
        version=INFO["version"],
        openapi_version="3.1.0",
        info={"description": INFO["description"]},
        servers=SERVERS,
        tags=TAGS,
        plugins=[FlaskPlugin()],
    )

    for nom, schema in COMPONENTS_SCHEMAS.items():
        spec.components.schema(nom, schema)
    for nom, schema in SECURITY_SCHEMES.items():
        spec.components.security_scheme(nom, schema)

    with app.test_request_context():
        for regle in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
            if regle.endpoint == "static":
                continue
            vue = app.view_functions[regle.endpoint]
            if not (vue.__doc__ and "---" in vue.__doc__):
                # Pas de bloc YAML : cette vue ne se documente pas elle-même
                # (voir docs.py) — rien à ajouter à la spec pour elle.
                continue
            spec.path(view=vue)

    return spec.to_dict()
