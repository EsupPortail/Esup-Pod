---
layout: default
version: 4.x
lang: en
---

# Elasticsearch Replacement Study

## Context

As part of the evolution of Esup-Pod, simplifying the technical architecture is an important goal to make the solution easier to install, maintain, and adopt across institutions.
Elasticsearch provides advanced search and indexing features, but operating it means deploying, configuring, monitoring, and maintaining an additional component.
However, the current search needs in Pod remain relatively controlled: full-text search on video metadata, filters, facets, pagination, and sorting. The usually observed volume, from a few thousand videos up to a projected maximum of around 50,000 to 100,000 entries, does not necessarily justify keeping a search engine as complete as Elasticsearch.
This study therefore aims to identify a lighter, free, open source solution that is more consistent with components already present or considered in the Pod ecosystem, especially Redis.

## Selected Solutions

The Esup-Pod project already uses Redis for some application purposes, especially caching. In the interest of simplifying the architecture, solutions related to the Redis ecosystem should therefore be prioritized.

The main solution studied is therefore **Redis Search with Redis 8**, ahead of Valkey Search, followed by native database solutions.

Redis 8 now includes RediSearch / Redis Search as a Redis Open Source component, alongside RedisJSON, RedisTimeSeries, and RedisBloom. Redis 8 is available under a tri-license including **AGPLv3**, **RSALv2**, and **SSPLv1**; since AGPLv3 is a recognized open source license, Redis Search can be considered an open source and free solution, subject to validation that AGPLv3 is acceptable for Esup-Pod.

### Recommended Ranking

| Priority | Solution                             | Positioning                                                                                 |
| -------: | ------------------------------------ | ------------------------------------------------------------------------------------------- |
|        1 | **Redis Search / Redis 8**           | Main recommended solution, consistent with Redis usage in Pod                                |
|        2 | **Valkey + Valkey Search**           | Close Redis alternative, community-driven, useful if the project wants to avoid AGPLv3       |
|        3 | **Native database search**           | Lightweight solution for small instances or minimal mode                                    |
|        4 | **Typesense**                        | Specialized open source alternative, but less consistent with the goal of building on Redis  |
|        5 | **OpenSearch**                       | Open source, but too close to Elasticsearch in complexity; not recommended in this context   |

Meilisearch is not selected as a main solution in this study in order to avoid any ambiguity related to its current licensing model.

---

## Solution 1 - Redis Search / Redis 8

### Principle

Redis Search makes it possible to use Redis as a full-text search engine. Redis Search supports fields of type `TEXT`, `TAG`, and `NUMERIC`, which maps well to Pod's needs: text search, exact filters, facets, and date filters.

Proposed configuration:

```ini
POD_SEARCH_ENGINE=redis
POD_SEARCH_REDIS_URL=redis://redis-search:6379/0
POD_SEARCH_INDEX=pod_videos
POD_SEARCH_PREFIX=pod:video:
POD_SEARCH_RESULTS_PER_PAGE=12
```

It is recommended to use a dedicated Redis instance for search:

```text
Pod
 |-- Redis cache
 |-- Redis Celery / broker, if Esup-Runner is not used
 `-- dedicated Redis Search
```

This avoids mixing cache, task queue, and search usage in the same Redis instance.

### Interest for Pod

Redis Search could replace the main Elasticsearch use cases:

* full-text search;
* multi-field search;
* field weighting;
* filters by type, discipline, channel, tag, language, curriculum;
* date filters;
* facets with counters;
* pagination;
* sorting by date;
* full reindexing.

Facets can be reproduced with `FT.AGGREGATE`, which supports `GROUPBY`-style grouping and counters through reducer functions such as `COUNT`.

Logical schema example:

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

Search example:

```bash
FT.SEARCH pod_videos "python @type_slug:{cours}" LIMIT 0 12
```

Facet example:

```bash
FT.AGGREGATE pod_videos "python" \
  GROUPBY 1 @type_slug \
  REDUCE COUNT 0 AS count \
  SORTBY 2 @count DESC \
  LIMIT 0 10
```

### Licensing Note

Redis Search / Redis 8 is free and open source under AGPLv3, but this license is more restrictive than a permissive license such as BSD, MIT, or Apache 2.0. This point must therefore be validated by the Esup-Portail project before making it the officially recommended dependency.

---

## Solution 2 - Valkey + Valkey Search

Valkey Search is an alternative close to the Redis ecosystem. Valkey Search can index data stored as Hash or JSON and supports full-text, numeric, and tag searches, as well as complex filters.

Possible configuration:

```ini
POD_SEARCH_ENGINE=valkey
POD_SEARCH_VALKEY_URL=redis://valkey-search:6379/0
POD_SEARCH_INDEX=pod_videos
POD_SEARCH_PREFIX=pod:video:
```

This solution is interesting if the project wants to stay within a Redis-compatible approach while avoiding discussions around the AGPLv3 license of Redis 8.

Main limitation: Valkey Search is a younger component than Redis Search. Its maturity, availability in distributions, and integration into environments used by institutions must therefore be checked.

---

## Solution 3 - Native Database Search

This solution consists of relying directly on the relational database.

Two main cases:

* PostgreSQL Full Text Search;
* MariaDB FULLTEXT.

PostgreSQL provides the `tsvector` and `tsquery` types for full-text search. MariaDB provides `MATCH ... AGAINST` to perform full-text search on columns indexed with a `FULLTEXT` index.

Possible configuration:

```ini
POD_SEARCH_ENGINE=database
POD_SEARCH_DATABASE_MODE=fulltext
```

This solution is relevant for:

* small instances;
* development environments;
* installations that want to avoid any additional service.

It is less suitable as the single main search engine because it handles facets, multi-field ranking, and future indexing of long transcriptions less naturally.

---

## Solution 4 - Typesense

Typesense is a specialized open source search engine. In particular, it provides typo tolerance, sorting, filtering, facets, and configurable ranking.

Possible configuration:

```ini
POD_SEARCH_ENGINE=typesense
POD_SEARCH_TYPESENSE_URL=http://typesense:8108
POD_SEARCH_TYPESENSE_COLLECTION=pod_videos
```

Typesense is technically interesting, but it adds an additional component with no direct link to Redis. In the context of Pod, it should therefore be considered an alternative, not the priority solution.

---

## Functional Comparison Table

Legend:

* **Yes**: feature well covered.
* **Partial**: possible, but with limits or additional development.
* **No**: not suitable or not easily available.

| Feature                                      |                         Redis Search / Redis 8 |                                  Valkey Search | PostgreSQL / MariaDB database |   Typesense |       OpenSearch |
| -------------------------------------------- | ---------------------------------------------: | ---------------------------------------------: | ----------------------------: | ----------: | ---------------: |
| Full-text search                             |                                            Yes |                                            Yes |                           Yes |         Yes |              Yes |
| Multi-field search                           |                                            Yes |                                            Yes |                           Yes |         Yes |              Yes |
| Field weighting                              |                                            Yes |                                            Yes |                       Partial |         Yes |              Yes |
| Exact filters                                |                                Yes, via `TAG` |                                  Yes, via tags |                           Yes |         Yes |              Yes |
| Date filters                                 |                            Yes, via `NUMERIC` |                                            Yes |                           Yes |         Yes |              Yes |
| Facets with counters                         |                       Yes, via `FT.AGGREGATE` |                                            Yes |                       Partial |         Yes |              Yes |
| Sorting by relevance                         |                                            Yes |                                            Yes |                       Partial |         Yes |              Yes |
| Sorting by date                              |                                            Yes |                                            Yes |                           Yes |         Yes |              Yes |
| Pagination                                   |                                            Yes |                                            Yes |                           Yes |         Yes |              Yes |
| Search with and without accents              |                              Partial, to test |                              Partial, to test |          Depends on database |         Yes |              Yes |
| Advanced French language analysis            |                                        Partial |                                        Partial |                       Partial |     Partial |              Yes |
| Typo tolerance                               |                                        Partial |                                        Partial |                 No or limited |         Yes |              Yes |
| Tag search                                   |                                            Yes |                                            Yes |                           Yes |         Yes |              Yes |
| Search on disciplines / channels / types     |                                            Yes |                                            Yes |                           Yes |         Yes |              Yes |
| Search in transcriptions                     | Yes, but memory usage must be watched carefully | Yes, but memory usage must be watched carefully |                       Partial |         Yes |              Yes |
| Future vector / semantic search              |                                            Yes |                                            Yes |       Partial with extensions |         Yes |              Yes |
| Ease of operation                            |                                           Good |                                           Good |                     Very good |       Good | Medium to weak |
| Memory usage                                 |                                         Medium |                                         Medium |                 Low to medium |     Medium |             High |
| Additional service                           |                                            Yes |                                            Yes |                            No |         Yes |              Yes |
| Consistency with Pod's Redis usage           |                                    Very strong |                                         Strong |                          Weak |       Weak |             Weak |
| Overall complexity                           |                                  Low to medium |                                  Low to medium |                           Low |     Medium |             High |
| Suitable for 50,000-100,000 videos           |                                            Yes |                             Yes, to benchmark |              Yes, depending on database |         Yes |              Yes |
| Recommended solution for Pod                 |                         **Yes, main choice** |                               Yes, alternative |             Yes, minimal mode | Alternative |  Not recommended |

---

## License and Operations Comparison Table

| Solution                    | License / status                             | Free of charge | Open source / free software | Note                                               |
| --------------------------- | -------------------------------------------- | -------------: | --------------------------: | -------------------------------------------------- |
| Redis Search / Redis 8      | AGPLv3 possible in the Redis 8 tri-license   |            Yes |             Yes under AGPLv3 | Excellent and integrated with Redis                |
| Valkey + Valkey Search      | Community open source ecosystem              |            Yes |                         Yes | Redis-compatible alternative                       |
| PostgreSQL Full Text Search | PostgreSQL License                           |            Yes |                         Yes | Very good if PostgreSQL is used                    |
| MariaDB FULLTEXT            | GPLv2                                        |            Yes |                         Yes | Very consistent if MariaDB remains the main DB     |
| Typesense                   | GPLv3                                        |            Yes |                         Yes | Good specialized engine, but additional service    |
| OpenSearch                  | Apache 2.0                                   |            Yes |                         Yes | Too close to Elasticsearch in complexity           |

---

## Recommendation

The main recommendation becomes:

```ini
POD_SEARCH_ENGINE=redis
POD_SEARCH_REDIS_URL=redis://redis-search:6379/0
POD_SEARCH_INDEX=pod_videos
```

Redis Search / Redis 8 should be positioned as the first solution because:

* Pod already uses Redis for caching;
* the solution reduces complexity compared with Elasticsearch;
* it keeps the important features: full-text search, filters, facets, sorting, pagination;
* it is suitable for a volume ranging from several thousand to 100,000 videos;
* it avoids introducing a completely different search engine.

The only caveat to document clearly is the license:

> Redis 8 / Redis Search can be used free of charge and can be used under the AGPLv3 open source license. However, this license must be validated by the Esup-Pod project before official adoption.

Valkey Search should be kept as a natural alternative if the project wants a Redis-compatible option with different governance.

Native database search should remain available as a minimal mode, but it should not be the main recommended engine for a new version of Pod.
