---
layout: default
version: 4.x
lang: fr
---

# Étude de remplacement d’Elasticsearch

## Contexte

Dans le cadre de l’évolution d’Esup-Pod, la simplification de l’architecture technique constitue un enjeu important pour faciliter l’installation, la maintenance et l’adoption de la solution par les établissements.
Elasticsearch apporte des fonctionnalités avancées de recherche et d’indexation, mais son exploitation implique une brique supplémentaire à déployer, configurer, superviser et maintenir.
Or, les besoins actuels de recherche dans Pod restent relativement maîtrisés : recherche plein texte sur les métadonnées des vidéos, filtres, facettes, pagination et tri. La volumétrie généralement observée, de quelques milliers de vidéos avec une projection maximale autour de 50 000 à 100 000 entrées, ne justifie pas nécessairement le maintien d’un moteur aussi complet qu’Elasticsearch.
Cette étude vise donc à identifier une solution plus légère, libre, gratuite et plus cohérente avec les composants déjà présents ou envisagés dans l’écosystème Pod, notamment Redis.

## Solutions retenues

Le projet Esup-Pod utilise déjà Redis pour certains usages applicatifs, notamment le cache. Dans une logique de simplification de l’architecture, les solutions en lien avec l’écosystème Redis doivent donc être privilégiées.

La solution principale étudiée est donc **Redis Search avec Redis 8**, devant Valkey Search, puis les solutions natives base de données.

Redis 8 intègre désormais RediSearch / Redis Search comme composant de Redis Open Source, au même titre que RedisJSON, RedisTimeSeries et RedisBloom. Redis 8 est proposé sous une tri-licence incluant **AGPLv3**, **RSALv2** et **SSPLv1** ; l’AGPLv3 étant une licence open source reconnue, Redis Search peut être considéré comme une solution open source et gratuite, sous réserve de validation de l’acceptabilité de l’AGPLv3 pour Esup-Pod.

### Classement recommandé

| Priorité | Solution                             | Positionnement                                                                                     |
| -------: | ------------------------------------ | -------------------------------------------------------------------------------------------------- |
|        1 | **Redis Search / Redis 8**           | Solution principale recommandée, cohérente avec l’usage de Redis dans Pod                          |
|        2 | **Valkey + Valkey Search**           | Alternative proche de Redis, communautaire, intéressante si l’on veut éviter la licence AGPLv3     |
|        3 | **Recherche native base de données** | Solution légère pour petites instances ou mode minimal                                             |
|        4 | **Typesense**                        | Alternative spécialisée open source, mais moins cohérente avec l’objectif de capitaliser sur Redis |
|        5 | **OpenSearch**                       | Open source, mais trop proche d’Elasticsearch en complexité ; non recommandé dans ce contexte      |

Meilisearch n’est pas retenu comme solution principale dans cette étude afin d’éviter toute ambiguïté liée à son modèle de licence actuel.

---

## Solution 1 — Redis Search / Redis 8

### Principe

Redis Search permet d’utiliser Redis comme moteur de recherche plein texte. Redis Search permet de déclarer des champs de type `TEXT`, `TAG` et `NUMERIC`, ce qui correspond bien aux besoins de Pod : recherche texte, filtres exacts, facettes et filtres de dates.

Configuration proposée :

```ini
POD_SEARCH_ENGINE=redis
POD_SEARCH_REDIS_URL=redis://redis-search:6379/0
POD_SEARCH_INDEX=pod_videos
POD_SEARCH_PREFIX=pod:video:
POD_SEARCH_RESULTS_PER_PAGE=12
```

Il est recommandé d’utiliser une instance Redis dédiée à la recherche :

```text
Pod
 ├── Redis cache
 ├── Redis Celery / broker, si non utilisation d'Esup-Runner
 └── Redis Search dédié
```

Cela évite de mélanger les usages cache, file de tâches et recherche dans une même instance Redis.

### Intérêt pour Pod

Redis Search permettrait de remplacer les usages principaux d’Elasticsearch :

* recherche plein texte ;
* recherche multi-champs ;
* pondération des champs ;
* filtres par type, discipline, chaîne, tag, langue, cursus ;
* filtres par date ;
* facettes avec compteurs ;
* pagination ;
* tri par date ;
* réindexation complète.

Les facettes peuvent être reproduites avec `FT.AGGREGATE`, qui permet des regroupements de type `GROUPBY` et des compteurs via des fonctions de réduction comme `COUNT`.

Exemple de schéma logique :

```bash
FT.CREATE pod_videos ON HASH PREFIX 1 pod:video: SCHEMA \
  title TEXT WEIGHT 2.0 \
  description TEXT WEIGHT 0.8 \
  owner_full_name TEXT WEIGHT 1.0 \
  tags_text TEXT WEIGHT 1.5 \
  type_title TEXT WEIGHT 1.0 \
  disciplines_text TEXT WEIGHT 1.0 \
  channels_text TEXT WEIGHT 0.8 \
  type_slug TAG \
  tags_slug TAG SEPARATOR "," \
  disciplines_slug TAG SEPARATOR "," \
  channels_slug TAG SEPARATOR "," \
  cursus TAG \
  main_lang TAG \
  site_id TAG \
  date_added_ts NUMERIC SORTABLE
```

Exemple de recherche :

```bash
FT.SEARCH pod_videos "python @type_slug:{cours}" LIMIT 0 12
```

Exemple de facette :

```bash
FT.AGGREGATE pod_videos "python" \
  GROUPBY 1 @type_slug \
  REDUCE COUNT 0 AS count \
  SORTBY 2 @count DESC \
  LIMIT 0 10
```

### Note licensing

Redis Search / Redis 8 est gratuit et open source sous AGPLv3, mais cette licence est plus contraignante qu’une licence permissive de type BSD, MIT ou Apache 2.0. Il faut donc valider ce point côté projet Esup-Portail avant d’en faire la dépendance officielle recommandée.

---

## Solution 2 — Valkey + Valkey Search

Valkey Search est une alternative proche de l’écosystème Redis. Valkey Search permet d’indexer des données stockées en Hash ou JSON et prend en charge les recherches full-text, numériques, par tags, ainsi que des filtres complexes.

Configuration possible :

```ini
POD_SEARCH_ENGINE=valkey
POD_SEARCH_VALKEY_URL=redis://valkey-search:6379/0
POD_SEARCH_INDEX=pod_videos
POD_SEARCH_PREFIX=pod:video:
```

Cette solution est intéressante si le projet souhaite rester dans une logique Redis-compatible tout en évitant les discussions autour de la licence AGPLv3 de Redis 8.

Limite principale : Valkey Search est une brique plus jeune que Redis Search. Il faut donc vérifier sa maturité, sa disponibilité dans les distributions et son intégration dans les environnements utilisés par les établissements.

---

## Solution 3 — Recherche native base de données

Cette solution consiste à s’appuyer directement sur la base relationnelle.

Deux cas principaux :

* PostgreSQL Full Text Search ;
* MariaDB FULLTEXT.

PostgreSQL fournit les types `tsvector` et `tsquery` pour la recherche plein texte. MariaDB propose `MATCH ... AGAINST` pour effectuer une recherche plein texte sur des colonnes indexées avec un index `FULLTEXT`.

Configuration possible :

```ini
POD_SEARCH_ENGINE=database
POD_SEARCH_DATABASE_MODE=fulltext
```

Cette solution est pertinente pour :

* les petites instances ;
* les environnements de développement ;
* les installations qui souhaitent éviter tout service supplémentaire.

Elle est moins adaptée comme moteur principal unique, car elle gère moins naturellement les facettes, le ranking multi-champs et l’évolution vers l’indexation des transcriptions longues.

---

## Solution 4 — Typesense

Typesense est un moteur de recherche open source spécialisé. Il propose notamment la tolérance aux fautes, le tri, le filtrage, les facettes et le ranking configurable.

Configuration possible :

```ini
POD_SEARCH_ENGINE=typesense
POD_SEARCH_TYPESENSE_URL=http://typesense:8108
POD_SEARCH_TYPESENSE_COLLECTION=pod_videos
```

Typesense est techniquement intéressant, mais il ajoute une brique supplémentaire sans lien direct avec Redis. Dans le contexte de Pod, il doit donc être vu comme une alternative, pas comme la solution prioritaire.

---

## Tableau comparatif fonctionnel

Légende :

* **Oui** : fonctionnalité bien couverte.
* **Partiel** : possible, mais avec limites ou développement complémentaire.
* **Non** : non adapté ou non disponible simplement.

| Fonctionnalité                              |                  Redis Search / Redis 8 |                           Valkey Search | Base de données PostgreSQL / MariaDB |   Typesense |       OpenSearch |
| ------------------------------------------- | --------------------------------------: | --------------------------------------: | -----------------------------------: | ----------: | ---------------: |
| Recherche full text                         |                                     Oui |                                     Oui |                                  Oui |         Oui |              Oui |
| Recherche multi-champs                      |                                     Oui |                                     Oui |                                  Oui |         Oui |              Oui |
| Pondération des champs                      |                                     Oui |                                     Oui |                              Partiel |         Oui |              Oui |
| Filtres exacts                              |                          Oui, via `TAG` |                           Oui, via tags |                                  Oui |         Oui |              Oui |
| Filtres par date                            |                      Oui, via `NUMERIC` |                                     Oui |                                  Oui |         Oui |              Oui |
| Facettes avec compteurs                     |                 Oui, via `FT.AGGREGATE` |                                     Oui |                              Partiel |         Oui |              Oui |
| Tri par pertinence                          |                                     Oui |                                     Oui |                              Partiel |         Oui |              Oui |
| Tri par date                                |                                     Oui |                                     Oui |                                  Oui |         Oui |              Oui |
| Pagination                                  |                                     Oui |                                     Oui |                                  Oui |         Oui |              Oui |
| Recherche avec accents / sans accents       |                        Partiel à tester |                        Partiel à tester |                    Dépend de la base |         Oui |              Oui |
| Analyse linguistique française avancée      |                                 Partiel |                                 Partiel |                              Partiel |     Partiel |              Oui |
| Tolérance aux fautes de frappe              |                                 Partiel |                                 Partiel |                        Non ou limité |         Oui |              Oui |
| Recherche sur tags                          |                                     Oui |                                     Oui |                                  Oui |         Oui |              Oui |
| Recherche sur disciplines / chaînes / types |                                     Oui |                                     Oui |                                  Oui |         Oui |              Oui |
| Recherche dans les transcriptions           | Oui, mais attention à la taille mémoire | Oui, mais attention à la taille mémoire |                              Partiel |         Oui |              Oui |
| Recherche vectorielle / sémantique future   |                                     Oui |                                     Oui |              Partiel avec extensions |         Oui |              Oui |
| Facilité d’exploitation                     |                                   Bonne |                                   Bonne |                           Très bonne |       Bonne | Moyenne à faible |
| Consommation mémoire                        |                                 Moyenne |                                 Moyenne |                     Faible à moyenne |     Moyenne |           Élevée |
| Service supplémentaire                      |                                     Oui |                                     Oui |                                  Non |         Oui |              Oui |
| Cohérence avec l’usage Redis de Pod         |                              Très forte |                                   Forte |                               Faible |      Faible |           Faible |
| Complexité globale                          |                        Faible à moyenne |                        Faible à moyenne |                               Faible |     Moyenne |           Élevée |
| Adapté à 50 000 – 100 000 vidéos            |                                     Oui |                      Oui, à benchmarker |                      Oui, selon base |         Oui |              Oui |
| Solution recommandée pour Pod               |                **Oui, choix principal** |                        Oui, alternative |                    Oui, mode minimal | Alternative |   Non recommandé |

---

## Tableau comparatif licences et exploitation

| Solution                    | Licence / statut                            | Gratuit | Open source / libre | Remarque                                           |
| --------------------------- | ------------------------------------------- | ------: | ------------------: | -------------------------------------------------- |
| Redis Search / Redis 8      | AGPLv3 possible dans la tri-licence Redis 8 |     Oui |     Oui sous AGPLv3 | Excellent et intégré Redis                         |
| Valkey + Valkey Search      | Écosystème communautaire open source        |     Oui |                 Oui | Alternative Redis-compatible                       |
| PostgreSQL Full Text Search | PostgreSQL License                          |     Oui |                 Oui | Très bon si PostgreSQL est utilisé                 |
| MariaDB FULLTEXT            | GPLv2                                       |     Oui |                 Oui | Très cohérent si MariaDB reste la base principale  |
| Typesense                   | GPLv3                                       |     Oui |                 Oui | Bon moteur spécialisé, mais service supplémentaire |
| OpenSearch                  | Apache 2.0                                  |     Oui |                 Oui | Trop proche d’Elasticsearch en complexité          |

---

## Recommandation

La recommandation principale devient :

```ini
POD_SEARCH_ENGINE=redis
POD_SEARCH_REDIS_URL=redis://redis-search:6379/0
POD_SEARCH_INDEX=pod_videos
```

Redis Search / Redis 8 doit être positionné en première solution, car :

* Pod utilise déjà Redis pour le cache ;
* la solution réduit la complexité par rapport à Elasticsearch ;
* elle conserve les fonctions importantes : recherche full text, filtres, facettes, tri, pagination ;
* elle est adaptée à une volumétrie de plusieurs milliers à 100 000 vidéos ;
* elle permet d’éviter l’introduction d’un moteur de recherche totalement différent.

La seule réserve à documenter clairement est la licence :

> Redis 8 / Redis Search est utilisable gratuitement et peut être utilisé sous licence open source AGPLv3. Cette licence doit toutefois être validée par le projet Esup-Pod avant adoption officielle.

Valkey Search doit être conservé comme alternative naturelle si le projet souhaite une option Redis-compatible avec une gouvernance différente.

La recherche native base de données doit rester disponible comme mode minimal, mais elle ne doit pas être le moteur principal recommandé pour une nouvelle version de Pod.
