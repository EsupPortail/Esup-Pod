#   TODO

- [ ] Comment ne pas renvoyer les paramètre sencibe via l'endpoint info/conf ? Pour cela mettre toutes les paramétrage sensible dans le .env puis vérifier dans les conf.py qu'on les définit pas. Ensuite le /info/conf utilise comme base de connaisance pour ces paramàtre que ce qui est définit dans les conf.py.
- [ ] Gestion du stockage des vidéo(file system + encodeur de loic) dans l'app encoding
- [ ] Avois dans les tests unitaire de vidéo que les test de vidéo donc pas de file système et encodage
- [ ] Dans l'app encoding avoir des test unitaire qui teste l'encodage via celry et le service d'encodage (il faut donc que le service d'encodage soit doimarrer que pour les tests) de meme pour celry et redis et la bdd. Cela mène a déplopper dans un premier temps une stack docker avec celry, redis et la bdd. puis avec le runner et mannager. Cela permetra de tester l'encodage de manière fiable et reproductible.

- [] Intérer les test comme dis précédament 
- Verifier la bonne utilisation optimiser de Redis et de Celery Pour l'encodage, et annalyse les problématique de disponibilité du manager comment on fait si il est pas la , des time oute ? etc 

