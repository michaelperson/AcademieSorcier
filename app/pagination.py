"""
Pagination minimaliste, partagée par les listings qui en ont besoin
(compétences par catégorie, tournois par année — jour 3). Faite à la main
avec count() + offset()/limit() plutôt qu'un plugin de pagination : deux
paramètres de requête (page, par_page) et une réponse enveloppée, pas
davantage.
"""

PAGE_PAR_DEFAUT = 1
PAR_PAGE_PAR_DEFAUT = 20
PAR_PAGE_MAX = 100


def _entier_positif(valeur, defaut):
    try:
        nombre = int(valeur)
    except (TypeError, ValueError):
        return defaut
    return nombre if nombre > 0 else defaut


def parametres_pagination(request):
    page = _entier_positif(request.args.get("page"), PAGE_PAR_DEFAUT)
    par_page = _entier_positif(request.args.get("par_page"), PAR_PAGE_PAR_DEFAUT)
    return page, min(par_page, PAR_PAGE_MAX)


def paginer(query, request, serialiseur):
    """`query` doit être une requête SQLAlchemy triée (l'ordre n'est pas
    garanti entre deux pages sans ORDER BY explicite côté appelant).
    """
    page, par_page = parametres_pagination(request)
    total = query.count()
    elements = query.offset((page - 1) * par_page).limit(par_page).all()
    pages = (total + par_page - 1) // par_page if par_page else 0

    return {
        "elements": [serialiseur(e) for e in elements],
        "page": page,
        "par_page": par_page,
        "total": total,
        "pages": pages,
    }
