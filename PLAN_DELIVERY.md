# NextWay — Plan : optimiseur de tournées de livraison

_Dernière mise à jour : 2026-06-27_

**Vision :** transformer NextWay (moteur de routing point-à-point) en **optimiseur de
tournées de livraison**. Cible démo : **Tunis**. Solveur d'optimisation : **Google OR-Tools**.
Objectif : portfolio solide, avec une vraie piste vers les boîtes de livraison tunisiennes.

> On ne refait rien à zéro. Le moteur existant (Dijkstra / A* / CH sur OSM) devient le
> **fournisseur de matrice de coûts**. OR-Tools devient le **cœur d'optimisation** par-dessus.

---

## Architecture cible

```
Frontend (carte Tunis)
   pose un dépôt + N points de livraison  →  bouton "Optimiser"
        |
   API (FastAPI)
   ├── /matrix    : matrice temps/distance entre tous les arrêts  → via le moteur (CH)
   ├── /optimize  : matrice → OR-Tools → ordre optimal des arrêts (+ contraintes)
   └── /route     : (existant) trace chaque segment réel entre 2 arrêts consécutifs
        |
   Moteur NextWay (graphe OSM Tunis + CH)        OR-Tools (solveur TSP/VRP)
```

Règle d'or (inchangée) : chaque couche ne connaît que celle du dessous. L'optimiseur
ne parle qu'à la matrice ; le frontend ne parle qu'à l'API.

---

## Phase D1 — Données Tunis
- [ ] Télécharger l'extrait OSM du Grand Tunis (Geofabrik "Tunisia", ou bbox Tunis via Overpass).
- [ ] Le charger dans le moteur existant (rien à changer : `NEXTWAY_OSM=data/tunis.osm`).
- [ ] Vérifier la couverture / qualité des routes sur la zone de démo.

## Phase D2 — Matrice de coûts (le pont moteur ↔ optimiseur)
- [ ] Endpoint `/matrix` : pour M arrêts (coords), renvoyer la matrice M×M des temps de trajet.
- [ ] Implémentation : snapper chaque arrêt, puis CH pour les trajets entre arrêts.
- [ ] Matrice **asymétrique** assumée (sens uniques) — OR-Tools gère.
- ⚠️ *Honnêteté perf :* M² plus courts chemins. Pour la démo (M ≤ ~50) c'est instantané.
      Pour de gros volumes, il faudra du "one-to-many" (Dijkstra multi-cibles) — plus tard.

## Phase D3 — Intégrer OR-Tools (le nouveau cœur)
- [ ] Ajouter `ortools` aux dépendances.
- [ ] Module `optimizer/` : prend (matrice, index du dépôt) → ordre des arrêts.
      Commencer en **TSP** (1 véhicule, départ/retour au dépôt).
- [ ] Endpoint `/optimize` : reçoit dépôt + livraisons → construit la matrice (D2) →
      appelle OR-Tools → renvoie l'ordre + distance/temps total.
- [ ] Interface propre pour étendre au multi-véhicules ensuite.

## Phase D4 — Frontend "tournée"
- [ ] Mode livraison : poser un **dépôt** + plusieurs **arrêts** sur la carte de Tunis.
- [ ] Bouton "Optimiser" → affiche la tournée **numérotée** (1, 2, 3…).
- [ ] Tracer les segments réels entre arrêts consécutifs (réutilise `/route`).
- [ ] Afficher distance/temps total, et la comparaison **"ordre saisi vs optimisé"**
      (le "−35 %" qui claque dans une démo).

## Phase D5 — Contraintes métier (montée en puissance → viser les boîtes)
- [ ] Plusieurs véhicules (**VRP**).
- [ ] Capacités (nb de colis par véhicule).
- [ ] Créneaux horaires (**VRPTW**).
- [ ] Retour au dépôt ou tournée ouverte.
- → OR-Tools gère tout ça nativement : c'est précisément pourquoi on l'a choisi.

## Phase D6 — Finitions portfolio
- [ ] Scénario de démo Tunis réaliste (1 dépôt + ~15 livraisons).
- [ ] README avec captures, "avant/après", explication de l'archi et des algos faits maison.
- [ ] (Optionnel) déploiement.

---

## Décisions déjà prises
- **Solveur :** Google OR-Tools (pas de TSP fait main).
- **Ville démo :** Tunis.
- **Saisie des points :** pins sur la carte / coordonnées GPS (réalité tunisienne :
  le géocodage d'adresses est peu fiable). Le système de clic existant colle déjà.

## Décisions à trancher au moment venu
- Tournée **avec retour au dépôt** (classique) ou **ouverte** (finir au dernier arrêt) ?
- Démarrer **1 véhicule (TSP)** puis passer au multi (VRP) — ordre conseillé.

---

## Ce qui est déjà fait et réutilisé (rien de perdu)
- Graphe OSM + parsing + cache. ✅
- Dijkstra / A* / **CH** (matrice de coûts rapide). ✅
- API FastAPI + frontend carte + snapping sur composante fortement connexe. ✅
- Auto-téléchargement OSM, un seul serveur, Makefile. ✅

L'optimiseur de livraison se construit **par-dessus** tout ça.
