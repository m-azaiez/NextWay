# NextWay — Plan de l'application

_Dernière mise à jour : 2026-06-26_

Objectif : transformer le moteur de routing en une **vraie app** : une carte web
où tu cliques deux points et l'itinéraire s'affiche, sur une **vraie carte de ville (OSM)**.

Approche retenue : **l'API d'abord, puis le frontend qui l'intègre.**

---

## Architecture cible

```
Navigateur (carte Leaflet)
        |  HTTP / JSON
        v
   API REST (FastAPI)  ──>  moteur nextway (Dijkstra / A*)  ──>  graphe OSM (en mémoire)
```

Règle d'or : chaque couche ne connaît que celle du dessous.
- Le **moteur** (déjà fait) ne sait rien de l'API.
- L'**API** ne sait rien du frontend.
- Le **frontend** ne parle qu'à l'API (jamais au moteur directement).

---

## Phase A — L'API REST (à faire en premier)

**Stack conseillé : FastAPI.** Pourquoi plutôt que Flask :
- validation automatique des entrées (Pydantic),
- doc interactive générée toute seule (`/docs`, Swagger) — pratique pour tester,
- async natif, prêt pour la perf plus tard.

### A.1 — Squelette
- [ ] Ajouter `fastapi` + `uvicorn` aux dépendances (`pyproject.toml` / `requirements.txt`).
- [ ] `src/nextway/api/app.py` : créer l'app FastAPI.
- [ ] Charger le graphe OSM **une seule fois au démarrage** (c'est coûteux, on le garde en mémoire — pas à chaque requête).
- [ ] Activer **CORS** (sinon le navigateur refusera d'appeler l'API).

### A.2 — Le problème clé : "snapping"
Quand l'utilisateur clique sur la carte, il ne tombe **jamais** pile sur un nœud du
graphe. Il faut donc trouver le nœud le plus proche d'une coordonnée cliquée.
- [ ] `src/nextway/core/spatial/nearest.py` : recherche du nœud le plus proche.
  - Version naïve : parcours linéaire (OK pour commencer).
  - Version rapide : **KD-tree** (`scipy.spatial.cKDTree`) ou une grille spatiale.

### A.3 — Les endpoints
- [ ] `GET /health` — vérifie que l'API tourne.
- [ ] `GET /nearest?lat=&lon=` — renvoie le nœud du graphe le plus proche d'un clic.
- [ ] `POST /route` — corps : `{start:{lat,lon}, goal:{lat,lon}, algo}`.
      Renvoie : la liste des points `[[lat,lon], ...]` + distance totale.
      Format conseillé : **GeoJSON LineString** (Leaflet le dessine directement).
- [ ] Gérer les cas : pas de route, point hors zone → codes HTTP propres (404/400).

### A.4 — Tests de l'API
- [ ] `tests/test_api.py` avec le `TestClient` de FastAPI : health, nearest, route valide, route impossible.

**Livrable Phase A : une API qu'on teste dans `/docs`, sans aucun frontend.**

---

## Phase B — Les vraies données (carte de ville)

- [ ] Télécharger un extrait OSM réel :
  - petite zone → **Overpass API** (bbox d'une ville),
  - région entière → **Geofabrik** (fichiers `.osm.pbf`).
- [ ] Vérifier que le parser actuel encaisse la taille. Si gros fichier `.pbf` →
      brancher `pyrosm`/`osmnx` derrière la même signature `(graph, coords)`.
- [ ] **Pré-calcul + cache** : parser une fois, sauvegarder le graphe (pickle), recharger vite.
      (Parser une ville à chaque démarrage = trop lent.)

---

## Phase C — Le frontend (l'app)

**Conseil pour apprendre : HTML + JS + Leaflet, sans build.** Simple, tu vois tout.
(React possible plus tard si tu veux.)

- [ ] `web/index.html` + `web/app.js` + Leaflet via CDN.
- [ ] Carte centrée sur la ville, tuiles OSM.
- [ ] Clic 1 = départ (marqueur A), clic 2 = arrivée (marqueur B).
- [ ] Appel `POST /route` → tracer la **polyline** de l'itinéraire.
- [ ] Afficher distance / temps estimé.
- [ ] États : "calcul en cours…", erreurs, bouton reset.

---

## Phase D — Intégration & finitions

- [ ] Brancher le frontend sur l'URL de l'API.
- [ ] Cas limites : clic hors zone, aucun itinéraire, double-clic.
- [ ] (Optionnel) bouton **"plus court" vs "plus rapide"** → nécessite la décision
      ci-dessous sur `Edge`.

---

## Phase E — Déploiement (plus tard)

- [ ] Conteneuriser (Docker).
- [ ] Servir le frontend statique depuis FastAPI, ou séparément.
- [ ] Déployer (Render, Fly.io, un VPS…).

---

## Décision à trancher maintenant

Pour proposer **"plus court" vs "plus rapide"**, il faut stocker dans `Edge` la
**distance** ET la **vitesse/temps** séparément (aujourd'hui il n'y a que `cost`).
C'est le bon moment : on le branche dans `cost.py` (le hook existe déjà) et tout
le reste suit. Si tu veux juste "le plus court" pour l'instant, on garde distance.

---

## Ordre d'attaque conseillé

1. **Phase A** (API sur le graphe démo qu'on a déjà) → valider toute la mécanique HTTP.
2. **Phase B** (vraies données OSM) → l'API route sur une vraie ville.
3. **Phase C + D** (le frontend) → l'app cliquable.
4. **Phase E** quand tout marche en local.

On garde le graphe démo au début de la Phase A : ça permet de construire et tester
l'API **sans attendre** le pipeline de données. On bascule sur l'OSM réel en Phase B.
