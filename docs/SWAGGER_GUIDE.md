# 📘 Guide de Documentation API (OpenAPI / Swagger)

Ce projet utilise drf-spectacular pour générer automatiquement une documentation interactive conforme à la spécification OpenAPI 3.0. 

Contrairement aux anciennes méthodes (doc écrite à la main), ici le code est la documentation. En annotant correctement vos Vues et Sérialiseurs Django, la documentation se met à jour automatiquement.

## 🚀 1. Accéder à la Documentation

Une fois le serveur lancé, trois interfaces sont disponibles :
| Interface  | URL | Usage  |
| ------------- |:-------------:| ------------- |
| Swagger UI      | URL/api/docs/     | Pour les Développeurs. Interface interactive permettant de tester les requêtes (GET, POST, DELETE...) directement depuis le navigateur.     |
| ReDoc      | URL/api/redoc/     | Pour les Lecteurs. Une présentation propre, hiérarchisée et moderne de tout le code.      |
| Schéma YAML      | URL/api/schema/    | Pour les Machines. Le fichier brut de la spécification. Utile pour générer automatiquement d'autres codes.      |


## 👨‍💻 2. Guide Développeur : Comment documenter ?

A. Documenter une Vue (Endpoint)

C'est l'étape la plus importante. On utilise le décorateur @extend_schema sur les méthodes du ViewSet.

A mettre avant la class dans la views.py :
```py
@extend_schema(tags=['Gestion des Vidéos'])  # 1. Groupe tous les endpoints sous ce Tag
```

A mettre sur chaque endpoint dans le views.py :
```py
    @extend_schema(
        summary="test",
        parameters=[
            OpenApiParameter(
                name='category', 
                description='Filtrer', 
                required=False, 
                type=str
            )],
        examples=[
            OpenApiExample(
                'Exemple Simple',
                value={
                    'title': 'test',
                    'url': 'localhost',
                    'description': 'test'
                }
            )
        ],
        responses={
            404: {"description": "Aucun trouvée"}
        }
    )
```

## 🚦 3. Bonnes Pratiques
Gérez les erreurs : Documentez toujours les cas d'erreurs (400, 403, 404) dans la section responses. Le front-end doit savoir à quoi s'attendre si ça échoue.

Utilisez des exemples : Pour les endpoints complexes (POST/PUT), utilisez OpenApiExample pour montrer un JSON valide.