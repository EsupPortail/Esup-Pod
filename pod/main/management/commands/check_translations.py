"""
Esup-pod check for missing translations.
"""

import glob
import sys

try:
    import polib
except ImportError as exc:
    raise SystemExit(
        "polib is required to run this translation check. "
        "Add polib to requirements-dev.txt."
    ) from exc

failed = False
for path in sorted(glob.glob("pod/locale/fr/LC_MESSAGES/*.po")):
    po = polib.pofile(path)

    for entry in po:
        if entry.obsolete:
            continue

        if entry.fuzzy:
            print(
                f"{path}:{entry.linenum or '?'}: fuzzy translation found "
                f"for msgid {entry.msgid!r}"
            )
            failed = True

        if not entry.translated():
            # skip the header entry, which is translated by po files themselves
            if entry.msgid == "":
                continue

            print(
                f"{path}:{entry.linenum or '?'}: untranslated entry found "
                f"for msgid {entry.msgid!r}"
            )
            failed = True

if failed:
    sys.exit(1)
