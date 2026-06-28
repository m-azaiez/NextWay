# NextWay — commandes pratiques
# Personnalise la zone et le fichier si besoin :
#   make city BBOX="48.85,2.34,48.88,2.38" OSM=data/paris.osm

OSM  ?= data/paris.osm
BBOX ?= 48.8156,2.2241,48.9021,2.4699   # Paris intra-muros (périphérique)
PORT ?= 8000

install:
	pip install -e ".[dev]"

test:
	pytest -q

# Lance l'app sur la grille démo (pas de données à télécharger).
demo:
	uvicorn nextway.api.app:app --reload --port $(PORT)

# Re-télécharge (supprime l'ancien fichier) puis lance — utile si tu changes la bbox.
fresh:
	rm -f $(OSM) $(OSM).cache.pkl
	$(MAKE) city

# Lance l'app sur une vraie ville : télécharge l'extrait OSM s'il manque,
# puis sert l'API + la carte sur http://127.0.0.1:$(PORT)
city:
	NEXTWAY_OSM=$(OSM) NEXTWAY_BBOX=$(BBOX) uvicorn nextway.api.app:app --reload --port $(PORT)

.PHONY: install test demo city fresh
