---
layout: default
version: 4.x
lang: fr
---

# Import depuis Panopto

Pour pouvoir importer des vidéos depuis Panopto, je vous conseille d’utiliser leur API SOAP. Il existe également une API REST, mais qui ne permet pas le téléchargement.

Voir la documentation de cette API PAnopto SOAP : [https://support.panopto.com/resource/APIDocumentation/Help/html/40d6edb9-fe7d-1db1-04a7-c3bffd218290.htm](https://support.panopto.com/resource/APIDocumentation/Help/html/40d6edb9-fe7d-1db1-04a7-c3bffd218290.htm)

Vous trouverez sur Github un exemple de script pour interroger leur API en python. (_attention : la branche Master est pour Python 2 et date de 2019. Utilisez plutôt la branche "python3" plus récente_).

À titre d’exemple, je vous partage les scripts que nous avons utilisés pour importer les sessions Panopto dans une base locale pivot, afin d’en exporter des fichiers json qu’on a ensuite importé dans Pod en suivant la doc Reprise de l’existant, entre la version 1.x et 2.x.

Ces scripts sont loin d’être parfaits, mais ils pourront peut-être vous servir de base si vous vous lancez dans cette tâche : [https://github.com/Badatos/panopto-soap](https://github.com/Badatos/panopto-soap)

> ⚠️ Cette migration a été réalisée en 2022, il est alors nécessaire de prendre en compte les changements de version de Pod et de Panopto lors de l’exécution de ce script.
