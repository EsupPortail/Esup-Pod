#!/usr/bin/env python3
"""
detect-french-django.py
Détecte les textes en français dans un projet Django : templates (.html)
et code Python (.py).

Utilisation :
  python3 detect-french-django.py [dossier=.] [--json rapport.json] [--html-only] [--py-only]

Sortie : regroupée par fichier ; dans un fichier, les textes identiques (même
orthographe, mêmes majuscules) sont regroupés avec leurs lignes.
Format d'affichage : texte, puis location(s).

Ce qui est ignoré automatiquement :
  - {% trans "..." %} / {% translate "..." %}         (déjà traduit)
  - {% blocktrans %}...{% endblocktrans %} (et blocktranslate)  (déjà traduit)
  - {# ... #} et {% comment %}...{% endcomment %}      (commentaires Django)
  - <!-- ... -->                                       (commentaires HTML)
  - <script>...</script> et <style>...</style>
  - _(...), gettext(...), gettext_lazy(...), pgettext(...), ngettext(...), etc. (déjà traduit)
  - docstrings de modules/fonctions/classes
  - dossiers : venv, env, .venv, __pycache__, node_modules, .git, migrations,
    locale, static, staticfiles, media, dist, build
"""
import ast
import bisect
import json
import os
import re
import sys

# ---------- Arguments ----------
args = sys.argv[1:]
json_out = None
if "--json" in args:
    i = args.index("--json")
    json_out = args[i + 1] if i + 1 < len(args) else "rapport.json"

html_only = "--html-only" in args
py_only = "--py-only" in args

skip_next = {json_out} if json_out else set()
positional = [a for a in args if not a.startswith("--") and a not in skip_next]
root = positional[0] if positional else "."

IGNORED_DIRS = {
    "venv", "env", ".venv", "__pycache__", "node_modules", ".git",
    "migrations", "locale", "static", "staticfiles", "media",
    "dist", "build", ".mypy_cache", ".pytest_cache",
}

# Fichiers à ne jamais analyser (ex : dictionnaires de traduction déjà en place)
IGNORED_FILES = {"detect-french-django.py", "constants.py"}

# ---------- Détection du français ----------
ACCENTS = re.compile(r"[àâäçéèêëîïôöûùüÿœæ]", re.I)
FR_WORDS = set("""
le la les des un une et ou pour avec dans sur est sont vous nous votre notre vos nos
ce cette ces mon ma mes ton ta tes leur leurs du au aux ne que qui quoi dont où
bonjour bonsoir merci bienvenue accueil connexion déconnexion inscription
valider annuler enregistrer supprimer modifier ajouter rechercher retour suivant
fermer ouvrir envoyer chargement erreur succès utilisateur mot passe nom prénom
adresse titre oui non aucun aucune tous toutes tout toute veuillez cliquez saisir
sélectionner choisir voir plus-tard compte panier commande paiement produit produits
""".split())

COMMENT_LIKE = re.compile(r"^(<!)?--[\s\S]*--(>)?$")
WORD_SPLIT = re.compile(r"[^a-zàâäçéèêëîïôöûùüÿœæ']+")
APOSTROPHE_PREFIX = re.compile(r"^[ldjnmst]'")


def is_french(text: str) -> bool:
    t = text.strip()
    if len(t) < 2:
        return False
    if re.fullmatch(r"[\W\d_]+", t):
        return False
    if re.match(r"^(https?:|/|\.|#|[a-z]+://)", t, re.I):
        return False
    if re.fullmatch(r"[a-z0-9_-]+", t) and t.lower() not in FR_WORDS:
        return False
    if COMMENT_LIKE.match(t):
        return False
    if ACCENTS.search(t):
        return True
    words = [w for w in WORD_SPLIT.split(t.lower()) if w]
    return any(APOSTROPHE_PREFIX.sub("", w) in FR_WORDS for w in words)


# ---------- Stockage des résultats (chaque occurrence, rangée par fichier) ----------
by_file = {}
total_occurrences = 0


def record(file, line, text):
    global total_occurrences
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean or not is_french(clean):
        return
    by_file.setdefault(file, []).append({"text": clean, "line": line})
    total_occurrences += 1


# ---------- Parcours des fichiers ----------
def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for fn in filenames:
            if fn in IGNORED_FILES:
                continue
            ext = os.path.splitext(fn)[1]
            if ext == ".py" and not html_only:
                yield os.path.join(dirpath, fn), "py"
            elif ext == ".html" and not py_only:
                yield os.path.join(dirpath, fn), "html"


# ---------- Analyse des fichiers Python ----------
TRANSLATION_FUNCS = {
    "_", "gettext", "gettext_lazy", "ugettext", "ugettext_lazy",
    "pgettext", "pgettext_lazy", "npgettext", "npgettext_lazy",
    "ngettext", "ngettext_lazy",
}


def analyze_py(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            source = f.read()
        tree = ast.parse(source, filename=path)
    except SyntaxError as e:
        print(f"⚠️  Impossible de parser {path}: {e}", file=sys.stderr)
        return

    excluded_positions = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else (
                func.attr if isinstance(func, ast.Attribute) else None
            )
            if name in TRANSLATION_FUNCS:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        excluded_positions.add((arg.lineno, arg.col_offset))

        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                doc = body[0].value
                excluded_positions.add((doc.lineno, doc.col_offset))

    # Clés de dictionnaires littéraux (ex: {"erreur": ...}) : jamais du texte affiché
    dict_key_positions = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    dict_key_positions.add((key.lineno, key.col_offset))

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            pos = (node.lineno, node.col_offset)
            if pos in excluded_positions or pos in dict_key_positions:
                continue
            record(path, node.lineno, node.value)


# ---------- Analyse des templates HTML ----------
TAG_RE = re.compile(r"<[^>]*>")
ATTR_RE = re.compile(
    r'\b(?:placeholder|title|alt|aria-label|value|label|content)\s*=\s*(".*?"|\'.*?\')',
    re.IGNORECASE,
)


def mask(text, pattern, flags=0):
    def repl(m):
        return "".join(c if c == "\n" else " " for c in m.group(0))
    return re.sub(pattern, repl, text, flags=flags)


def build_line_index(text):
    starts = [0]
    for m in re.finditer(r"\n", text):
        starts.append(m.end())
    return starts


def line_of(offset, line_starts):
    return bisect.bisect_right(line_starts, offset)


def analyze_html(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    text = mask(text, r"<!--.*?-->", re.S)                                    # commentaires HTML
    text = mask(text, r"{#.*?#}", re.S)                                       # commentaires Django
    text = mask(text, r"{%\s*comment\s*%}.*?{%\s*endcomment\s*%}", re.S | re.I)
    text = mask(text, r"<script\b[^>]*>.*?</script>", re.S | re.I)
    text = mask(text, r"<style\b[^>]*>.*?</style>", re.S | re.I)
    # Blocs déjà marqués pour traduction : on masque tout le bloc (tags + contenu)
    text = mask(
        text,
        r"{%\s*blocktrans(?:late)?\b.*?%}.*?{%\s*endblocktrans(?:late)?\s*%}",
        re.S | re.I,
    )
    # Tags Django restants ({% trans "..." %}, {% if %}, {% for %}, ...) et variables {{ ... }}
    text = mask(text, r"{%.*?%}", re.S)
    text = mask(text, r"{{.*?}}", re.S)

    line_starts = build_line_index(text)

    for m in ATTR_RE.finditer(text):
        value = m.group(1)[1:-1]
        record(path, line_of(m.start(1), line_starts), value)

    pos = 0
    for m in TAG_RE.finditer(text):
        chunk = text[pos:m.start()]
        if chunk.strip():
            first_char = pos + (len(chunk) - len(chunk.lstrip()))
            record(path, line_of(first_char, line_starts), chunk)
        pos = m.end()
    chunk = text[pos:]
    if chunk.strip():
        first_char = pos + (len(chunk) - len(chunk.lstrip()))
        record(path, line_of(first_char, line_starts), chunk)


# ---------- Main ----------
if not os.path.isdir(root):
    print(f"Dossier introuvable : {root}", file=sys.stderr)
    sys.exit(1)

for file, kind in walk(root):
    if kind == "py":
        analyze_py(file)
    else:
        analyze_html(file)

files = sorted(by_file.keys())
for file in files:
    print(f"\n📄 {file}")
    occurrences = sorted(by_file[file], key=lambda o: o["line"])
    for occ in occurrences:
        print(f"  texte:    {occ['text']}")
        print(f"  location: {file}:{occ['line']}")

print(f"\n✅ {total_occurrences} occurrence(s) dans {len(files)} fichier(s).")

if json_out:
    report = [
        {
            "file": file,
            "occurrences": [
                {"text": o["text"], "location": f"{file}:{o['line']}"}
                for o in sorted(by_file[file], key=lambda o: o["line"])
            ],
        }
        for file in files
    ]
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📝 Rapport écrit dans {json_out}")