"""Build the tactical_breach_wizards .apworld AND install it into custom_worlds.

This is the one command between "I edited the world source" and "Archipelago uses it":

    python build_apworld.py [output_dir]

It zips the ``tactical_breach_wizards/`` source folder (next to this script) into
``tactical_breach_wizards.apworld`` and writes it — by default — one level up, i.e.
directly into ``custom_worlds/``, which IS the installed location Archipelago loads
from. (This frozen Archipelago build can only load zipped .apworld files from
custom_worlds, not unpacked folders — that's why the source hides in this
underscore-prefixed dev folder, which Archipelago ignores.)

To share the world with other players, send them the same .apworld file; they
double-click it or drop it into their own ``custom_worlds/``.

An .apworld is just a zip whose single top-level entry is the world package directory,
plus the ``archipelago.json`` manifest at the archive root.
"""

import sys
import zipfile
from pathlib import Path

PACKAGE = "tactical_breach_wizards"
# Files/dirs we never want inside the shipped apworld.
EXCLUDE_SUFFIXES = (".pyc",)
EXCLUDE_DIRS = {"__pycache__"}


def main() -> None:
    here = Path(__file__).resolve().parent
    pkg_dir = here / PACKAGE
    if not pkg_dir.is_dir():
        raise SystemExit(f"package directory not found: {pkg_dir}")

    # Default output = custom_worlds/ itself: building IS installing.
    out_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else here.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{PACKAGE}.apworld"

    count = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # archipelago.json manifest goes at the archive root (AP scans for any entry
        # ending in "archipelago.json"). Required from AP 0.7.0 onward.
        manifest = here / "archipelago.json"
        if manifest.is_file():
            zf.write(manifest, "archipelago.json")
            count += 1
        for path in sorted(pkg_dir.rglob("*")):
            if path.is_dir():
                if path.name in EXCLUDE_DIRS:
                    continue
                continue
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            if path.suffix in EXCLUDE_SUFFIXES:
                continue
            arcname = path.relative_to(here)  # keeps the leading "tactical_breach_wizards/"
            zf.write(path, arcname.as_posix())
            count += 1

    print(f"wrote {out_path} ({count} files)")


if __name__ == "__main__":
    main()
