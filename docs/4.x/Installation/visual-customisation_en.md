---
layout: default
version: 4.x
lang: en
---

# Visual customisation

## Modify the school logo

You can display your school’s logo at the bottom of the page.

To do this, place your logo in the `pod/main/static/custom/img/` folder, and enter its path in the `settings_local.pyv :

```python
TEMPLATE_VISIBLE_SETTINGS = {
  ...
  'LOGO_ETB': 'custom/img/logo_my_etab.svg',
  ...
}
```

### If you have a coloured school logo

We suggest that you also provide a 2nd "dark mode" version of your logo, which will provide sufficient contrast on dark backgrounds. Place the file in the same folder as the first, then in your custom CSS file (see "Changing Pod’s main colours" below) enter the following:

```css
[data-theme="dark"] .pod-footer-logo {
  background-image: url("/static/custom/img/my-white-logo.svg") !important;
}
```

### If your school logo is monochrome

You can use just one file, and invert the colours in your custom CSS as follows:

```css
[data-theme="dark"] .pod-footer-logo {
 filter: invert(100);
}
```

---

## Change the main Pod colours

To customise the look of your Pod server, you can add your own style sheet, by specifying this in the `settings_local.py` file:

```python
TEMPLATE_VISIBLE_SETTINGS = {
  ...
  'CSS_OVERRIDE': 'custom/theme-mon_etab.css',
  ...
}
```

Place a `theme-mon_etab.css` file in the `pod/main/static/custom/` folder.

In this file, you can change the Pod colours. Here are a few examples:

### Lille green

```css
/*** Esup Pod custom CSS ***/
:root {
 /* example green univ-lille.fr 2022 */
  --pod-primary: #1F8389;
  --pod-primary-lighten: #08b0a0;
  --pod-primary-darken: #18575D;

  /* Dark mode */
  --pod-primary-dark: #1F8389;
  --pod-primary-lighten-dark: #18575D;
  --pod-primary-darken-dark: #08b0a0;
}
```

### Rose "Pod v2"

```css
/*** Esup Pod custom CSS ***/
:root {
 /* example rose "pod v2" */
  --pod-primary: #ae2573;
  --pod-primary-lighten: #d782b3;
  --pod-primary-darken: #93326a;

  /* Dark mode */
  --pod-primary-dark: #ae2573;
  --pod-primary-lighten-dark: #db258e;
  --pod-primary-darken-dark: #93326a;
}
```

### Violet "BS 5

```css
/*** Esup Pod custom CSS ***/
:root {
 /* purple example "BS 5" */
  --pod-primary: #7952b3;
  --pod-primary-lighten: #ad76ff;
  --pod-primary-darken: #6528e0;

  /* Dark mode */
  --pod-primary-dark: #7952b3;
  --pod-primary-lighten-dark: #ad76ff;
  --pod-primary-darken-dark: #6528e0;
}
```

### "default" Blue

```css
/*** Esup Pod custom CSS ***/
:root {
  /* blue ‘default’ example */
  --pod-primary: #0052cc;
  --pod-primary-lighten: #0065ff;
  --pod-primary-darken: #0048b4;

  /* Dark Mode */
  --pod-primary-dark: #0052cc;
  --pod-primary-lighten-dark: #0065ff;
  --pod-primary-darken-dark: #0048b4;
}
```

---

## Modify the Pod "favicon" icon

You can change the default favicon displayed by Pod by specifying the following in the `settings_local.py` file:

```python
TEMPLATE_VISIBLE_SETTINGS = {
  ...
  'FAVICON': 'img/logoPod.svg',
  ...
}
```

We strongly recommend that you use the svg format for this icon, as this format makes it easy to manage colour variants for an Internet browser in dark mode. If you look at the `main/static/img/pod_favicon.svg` file for example, you’ll see the following instructions:

```css
@media (prefers-color-scheme: dark) { :root { fill: #FFF }}
@media (prefers-color-scheme: light) { :root { fill: #000 }}
```

These can be used to manage 2 different sets of colours in the same logo, allowing good contrast to be maintained whatever the background colour. Don’t hesitate to use them as inspiration when creating your own `favicon.svg`.

---

## Use the same image as a logo and favicon

It’s perfectly possible to use the same image, but if your image has 2 sets of colours, I suggest you add the following CSS lines (or use them as inspiration) in your custom CSS file so that it is always displayed in contrast on Pod :

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

## Useful commands

Depending on your environment, once you have made these changes, don’t forget to :

- deploy static files (CSS, images, etc.) using the command :

```bash
(django_pod4) pod@pod-:~/django_projects/podv4$ make statics
```

- restart the various services affected, typically the uwsgi-pod service on your web servers:

```bash
pod@pod-:~/django_projects/podv4$ sudo systemctl restart uwsgi-pod
```
