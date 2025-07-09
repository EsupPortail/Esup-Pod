---
layout: default
version: 4.x
lang: fr
---

# Personnalisation visuelle

## Modifier le logo de l'établissement

Vous pouvez faire apparaitre en bas de page le logo de votre établissement.

Pour cela, placez votre logo dans le dossier `pod/main/static/custom/img/`, et indiquez son chemin dans le fichier `settings_local.pyv :

```python
TEMPLATE_VISIBLE_SETTINGS = {
...
'LOGO_ETB': 'custom/img/logo_mon_etab.svg',
...
}
```

### Si vous avez un logo d'établissement coloré

Nous vous invitons à prévoir également une 2e version "mode sombre" de votre logo, qui sera suffisamment contrastée sur fonds foncés. Placez le fichier dans le même dossier que le premier, puis dans votre fichier CSS personnalisé (voir "Changer les couleurs principales de Pod" ci-dessous) indiquez ceci :

```css
[data-theme="dark"] .pod-footer-logo {
  background-image: url('/static/custom/img/logo_mon_etab_blanc.svg') !important;
}
```

### Si votre logo d'établissement est monochrome

Vous pouvez n'utiliser qu'un fichier, et en inverser les couleurs dans votre CSS personnalisé ainsi :

```css
[data-theme="dark"] .pod-footer-logo {
  filter: invert(100);
}
```

---

## Changer les couleurs principales de Pod

Pour personnaliser le look de votre serveur Pod, vous pouvez ajouter votre propre feuille de style, en indiquant ceci dans le fichier `settings_local.py` :

```python
TEMPLATE_VISIBLE_SETTINGS = {
...
'CSS_OVERRIDE': 'custom/theme-mon_etab.css',
...
}
```

Placez alors un fichier `theme-mon_etab.css` dans le dossier `pod/main/static/custom/`

Dans ce dernier, vous pouvez modifier les couleurs de Pod. Voici quelques exemples :

### Vert Lillois

```css
/*** Esup Pod custom CSS ***/
:root {
  /* exemple vert univ-lille.fr 2022 */
  --pod-primary: #1F8389;
  --pod-primary-lighten: #08b0a0;
  --pod-primary-darken: #18575D;

  /* Mode sombre */
  --pod-primary-dark: #1F8389;
  --pod-primary-lighten-dark: #18575D;
  --pod-primary-darken-dark: #08b0a0;
}
```

### Rose "Pod v2"

```css
/*** Esup Pod custom CSS ***/
:root {
  /* exemple rose "pod v2" */
  --pod-primary: #ae2573;
  --pod-primary-lighten: #d782b3;
  --pod-primary-darken: #93326a;

  /* Mode sombre */
  --pod-primary-dark: #ae2573;
  --pod-primary-lighten-dark: #db258e;
  --pod-primary-darken-dark: #93326a;
}
```

### Violet "BS 5"

```css
/*** Esup Pod custom CSS ***/
:root {
  /* exemple violet "BS 5" */
  --pod-primary: #7952b3;
  --pod-primary-lighten: #ad76ff;
  --pod-primary-darken: #6528e0;

  /* Mode sombre */
  --pod-primary-dark: #7952b3;
  --pod-primary-lighten-dark: #ad76ff;
  --pod-primary-darken-dark: #6528e0;
}
```

### Bleu "default"

```css
/*** Esup Pod custom CSS ***/
:root {
  /* exemple bleu "default" */
  --pod-primary: #0052cc;
  --pod-primary-lighten: #0065ff;
  --pod-primary-darken: #0048b4;

  /* Mode sombre */
  --pod-primary-dark: #0052cc;
  --pod-primary-lighten-dark: #0065ff;
  --pod-primary-darken-dark: #0048b4;
}
```

---

## Modifier l’icône "favicon" de Pod

Il est possible de modifier le logo par défaut affiché en favori par Pod, en indiquant ceci dans le fichier `settings_local.py` :

```python
TEMPLATE_VISIBLE_SETTINGS = {
...
'FAVICON': 'img/logoPod.svg',
...
}
```

Nous vous conseillons fortement le format svg pour cette icone, car ce format permet de gérer facilement des variantes de couleurs pour un navigateur Internet en mode sombre. En regardant le fichier `main/static/img/pod_favicon.svg` par exemple, vous verrez les instructions suivantes :

```css
@media (prefers-color-scheme: dark)  { :root { fill: #FFF }}
@media (prefers-color-scheme: light) { :root { fill: #000 }}
```

Ces dernières permettent de gérer 2 jeux de couleurs différents dans le même logo, permettant de conserver un bon contraste quel que soit la couleur de fond. N'hésitez-pas à vous en inspirer si vous créez votre propre `favicon.svg`.

---

## Utiliser la même image comme logo et comme favicon

C'est tout à fait possible d'utiliser la même image, mais si votre image comprend 2 jeux de couleurs, je vous invite à ajouter les lignes CSS suivantes (ou à vous en inspirer) dans votre fichier CSS personnalisé pour que celle-ci s'affiche toujours contrastée sur Pod :

```css
/* When your logo.svg already switch color on browser color-scheme: dark */
@media (prefers-color-scheme: light) {
  [data-theme="dark"] .pod-navbar__brand img{
    filter: invert(100%) saturate(2908%) hue-rotate(27deg) brightness(121%) contrast(99%);
  }
}
@media (prefers-color-scheme: dark) {
  [data-theme="light"] .pod-navbar__brand img{
    filter: invert(100%) saturate(2908%) hue-rotate(27deg) brightness(121%) contrast(99%);
  }
}
```

## Commandes utiles

Selon votre environnement, après avoir réalisé ces modifications, n'oubliez pas de :

- déployer les fichiers statiques (CSS, images...) via la commande :

```bash
(django_pod4) pod@pod-:~/django_projects/podv4$ make statics
```

- redémarrer les différents services impactés, typiquement le service uwsgi-pod de vos servurs Web :

```bash
pod@pod-:~/django_projects/podv4$ sudo systemctl restart uwsgi-pod
```
