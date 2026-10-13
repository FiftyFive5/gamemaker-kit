---
name: gm-project-tools
description: >
  This skill should be used for project-wide work on a GameMaker project: "show me my project",
  "project overview/map", "which assets are unused", "clean up unused sprites", "rename obj_x to obj_y",
  "rename this sprite everywhere", "import my Aseprite animations", "import this folder of sprites",
  "turn these PNGs into sprites", "translate my game", "add Turkish/English language support",
  "localization", "extract text for translation".
metadata:
  version: "0.1.0"
---

# Project-wide tools

All commands are subcommands of `<plugin>/skills/gamemaker-assets/scripts/gm.py`. Each accepts `--dry-run`.
Run `check_project.py` afterwards and tell the user to reload the project in the IDE (close it first for
rename).

## Project map

```bash
python3 gm.py map <project> [-o project-map.html]
```

Writes a self-contained HTML page: object cards with sprite thumbnails, events, line counts and where they are
placed; inheritance tree; rooms in order with instance counts; sprites and who uses them; scripts with their
functions and callers; possibly unused assets; checker errors. Searchable, light/dark. Send the file to the
user (it opens in any browser) and summarise two or three things worth their attention (unused assets,
objects with no events, scripts nothing calls).

## Unused assets

```bash
python3 gm.py unused <project>                          # list
python3 gm.py unused <project> --remove spr_old,obj_test
python3 gm.py unused <project> --remove all
```

An asset counts as used if any GML mentions its name (including in strings), any `.yy` references it (object
sprite, parent, room instance, tileset…), or — for scripts — any of its functions is called elsewhere. Rooms,
tilesets, notes and extensions are never listed. Names built at runtime (`asset_get_index("spr_" + name)`)
are invisible to this check, so **always show the list to the user and get explicit confirmation of which
assets to remove**. Removal unregisters the asset and moves its folder to `_gmkit_removed/` in the project, so
it can be restored by hand.

## Rename everywhere

```bash
python3 gm.py rename <project> obj_maymun obj_monkey
```

Renames the folder and files, all `.yy`/`.yyp` references (parents, sprite links, collision events, room
instances) and whole-word GML uses, plus `Collision_<old>.gml` files in other objects. It changes strings and
comments containing the name too — mention that. The folder is renamed first; if that fails nothing is
written. The GameMaker IDE must be closed (or reloaded afterwards).

## Bulk sprite import

```bash
python3 gm.py import-aseprite <project> monkey.json --prefix spr_monkey --origin bottom-centre
python3 gm.py import-folder   <project> art/ --fps 10 --origin bottom-centre
```

- Aseprite: export with **File → Export Sprite Sheet**, JSON data on (hash or array), tags included; trimmed
  frames are restored to full size. Each tag becomes `<prefix>_<tag>` (forward, reverse and ping-pong
  respected) with fps derived from frame durations. Without tags, one sprite.
- Folder: each sub-folder of PNGs, or each group of files named `walk_0.png, walk_1.png…`, becomes
  `spr_<name>`.
- Frames within one sprite must be the same size. Needs Pillow.

## Localization

```bash
python3 gm.py extract-strings <project> --langs tr          # collect into localization.csv
python3 gm.py extract-strings <project> --apply             # replace text in code with tr("key")
python3 gm.py build-lang <project>                          # after filling translations in the CSV
```

Finds player-facing literals passed to `draw_text*`, `show_message`, `show_question` and `juice_text`,
merges them into `localization.csv` (key, source language, other languages) and generates `scr_lang` with
`tr(key)`, `lang_set("tr")` and `lang_list()`. Missing translations fall back to the source text.

Workflow to offer: run extract without `--apply`, show the user the keys, fill in translations yourself if
asked (keep `\n` escapes and placeholders intact), then `--apply` and `build-lang`. Text built with
concatenation (`"Score: " + string(score)`) is extracted as its literal part only — suggest restructuring
such lines (e.g. `tr("score") + string(score)`).
