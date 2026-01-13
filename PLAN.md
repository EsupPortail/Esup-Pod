1. Contextualisation du Projet POD V5 (Révisée)
Objectif Principal : Opérer une refonte architecturale majeure de la plateforme Esup-Pod pour passer d'une application monolithique (V4) à une architecture distribuée et découplée (V5). L'objectif est de transformer le backend Django en un fournisseur de services (API) agnostique du frontend.

Architecture Cible :

Frontend (Hors périmètre) : Application cliente séparée (SPA/Client riche) consommant l'API.

Encodage (Existant/Externe) : Service autonome conteneurisé piloté par files d'attente.

Backend (Périmètre Équipe) : API RESTful (Django/DRF) gérant les données, la logique métier, la sécurité et l'orchestration.

Contraintes Techniques :

API First : Toutes les données et actions doivent être accessibles via JSON.

Statelessness : L'authentification doit être adaptée à un client détaché (Token/Session via API).

Compatibilité : Le backend doit servir les médias et métadonnées de manière standardisée pour n'importe quel client (Web, Mobile, LMS).

2. Périmètre Fonctionnel du Backend V5
Le backend V5 se déleste du rendu HTML (sauf administration) pour se concentrer sur quatre piliers :

Exposition API (REST) : Fournir les endpoints CRUD pour les ressources (Vidéos, Users, Channels).

Orchestration des Workflows : Gérer le cycle de vie d'une vidéo (Upload -> Encodage -> Publication).

Sécurité & Permissions : Qui peut uploader ? Qui peut voir ? (Logique fine des ACLs).

Distribution de Contenu : Servir les manifestes de lecture (HLS/DASH) et les fichiers statiques sécurisés.

3. Cahier des Charges - Backend POD V5 (Focus Refonte)
Voici les fonctionnalités backend à implémenter ou adapter, classées par module technique.

A. Architecture API (Module pod.main & rest_views)
Objectif : Remplacer les Vues Django classiques (TemplateView) par des Vues REST.

À faire :

[ ] Standardisation des réponses : Définir une enveloppe JSON standard (status, data, errors) pour tous les endpoints.

[ ] Documentation (Swagger/OpenAPI) : Générer automatiquement la doc API pour l'équipe Frontend (drf-spectacular ou yasg souvent utilisé).

[ ] Gestion des erreurs : Remplacer les pages d'erreur HTML (404/500) par des codes d'erreur JSON précis.

B. Authentification & Sécurité (Module pod.authentication)
Objectif : Sécuriser les appels API provenant du Frontend séparé.

À faire :

[ ] Mécanisme d'Auth : Implémenter/Vérifier l'authentification par Token (JWT ou Auth Token DRF) ou Session sécurisée avec CORS configuré.

[ ] CORS Headers : Configurer django-cors-headers pour autoriser le domaine du nouveau Frontend.

[ ] Protection CSRF : Adapter la validation CSRF pour les appels AJAX/Fetch du frontend.

C. Gestion des Médias & Upload (Module pod.video)
Objectif : Gérer l'ingestion de fichiers sans formulaire HTML classique.

À faire :

[ ] API Upload Résilient : Endpoint acceptant le Chunked Upload (découpage de fichiers lourds) pour éviter les timeouts serveur.

[ ] Validation de fichiers : Vérification stricte des types MIME et extensions côté API avant acceptation.

[ ] Lien avec Stockage : Abstraction du système de fichiers (Local vs S3) pour préparer l'évolutivité.

D. Orchestration Encodage (Module pod.video_encode_transcript)
Objectif : Le backend est le chef d'orchestre, pas l'ouvrier.

À faire :

[ ] Trigger Encodage : Une fois l'upload API terminé, déclencher la tâche Celery d'envoi vers le service d'encodage.

[ ] API Callbacks : Créer un endpoint sécurisé (ex: /api/internal/encoding-callback/) que le service d'encodage appelle pour notifier le succès/échec.

[ ] Statut en temps réel : Exposer l'état de l'encodage (ex: "processing", "ready") dans le JSON de l'objet Video.

E. Diffusion & Player (Configuration)
Objectif : Fournir les données brutes au player JS du frontend.

À faire :

[ ] API Config Player : Un endpoint (ex: /api/videos/{id}/config) renvoyant toutes les URL nécessaires : flux vidéo, pistes de sous-titres (VTT), chapitrage, poster.

[ ] Sécurisation des Assets : Si les vidéos sont privées, l'API doit générer des URLs signées ou vérifier les sessions sur l'accès aux fichiers statiques (X-Sendfile / X-Accel-Redirect).