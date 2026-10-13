---
name: gamemaker-assets
description: >
  This skill should be used whenever Claude creates, edits, renames or registers files inside a GameMaker
  project folder (a folder containing a .yyp file): "add a new object", "create an enemy", "add a Step/Draw/
  Collision event", "import these sprites", "add a script", "register it in the project", "the IDE says the
  project is later than this release", "GameMaker won't open my project after the edit", or any task that writes
  .yy, .yyp or event .gml files directly instead of through the GameMaker IDE.
metadata:
  version: "0.1.0"
---

# GameMaker project assets

GameMaker stores every asset as a `.yy` file (JSON-like) plus files next to it, and lists every asset in the
project's `.yyp`. The `.yy` format is not officially documented and changes between IDE releases: type tags,
`resourceVersion` values, key order and even which keys exist differ across versions, and newer IDEs reject
files they consider malformed. Any template remembered from training data or the internet is likely to be for
a different version than the user's.

## Use the scaffolding script first

`scripts/gm.py` (in this skill's folder) does the rule below automatically for the common cases and refuses —
writing nothing — whenever it cannot reproduce the project's own file layout exactly:

```bash
python3 <skill>/scripts/gm.py info <project>
python3 <skill>/scripts/gm.py new-object <project> obj_enemy --events Create,Step,Draw,Collision:obj_wall \
        --sprite spr_enemy --folder Enemies [--parent obj_enemy_base] [--persistent]
python3 <skill>/scripts/gm.py add-event  <project> obj_enemy Alarm0 EndStep DrawGUI User0 KeyPress:space
python3 <skill>/scripts/gm.py new-script <project> scr_helpers
python3 <skill>/scripts/gm.py new-sprite <project> spr_enemy_walk --sheet walk.png --frame-w 32 --frame-h 32 \
        --origin bottom-centre        # or: --frames f1.png f2.png ...
```

Add `--dry-run` to see what would be written. Event names: Create, Destroy, CleanUp, Step, BeginStep, EndStep,
Draw, DrawGUI, DrawBegin, DrawEnd, Alarm0–11, User0–15, RoomStart, RoomEnd, GameStart, GameEnd, AnimationEnd,
Collision:<object>, KeyPress:<key>, KeyRelease:<key>, Keyboard:<key>. `new-sprite` needs Pillow
(`python3 -m pip install Pillow`); it slices sheets, drops empty trailing cells, and writes both the frame and
layer images.

More commands live in the same script — playable starter kit and drop-in systems (`gm-starter` skill),
project map, unused assets, rename, Aseprite/folder import and localization (`gm-project-tools` skill).
`python3 <skill>/scripts/gm.py -h` lists them all.

When the script refuses, read its reason and follow it (usually: add one asset or event of that kind in the IDE
so a template exists, or pass `--template` with an asset that has the needed content). Fall back to manual edits
following the rule below only for things the script does not cover (rooms, sounds, renames). Run
`check_project.py` after either path.

## The rule: the project is the template

Never write a `.yy` file or a `.yyp` entry from memory. Every new asset is a copy of an existing asset of the
same type **from this project**, with only the identifying fields changed.

1. Find the project root: the folder holding exactly one `*.yyp`. Read its `MetaData.IDEVersion` (when present)
   and mention the version to the user once.
2. Find a template of the same type in the project (`objects/*/*.yy` for objects, `sprites/*/*.yy`, `scripts/*/*.yy`,
   `rooms/*/*.yy`, …). Prefer the simplest one (fewest events, one frame).
3. If no asset of that type exists yet, stop and ask the user to create one empty asset of that type in the IDE
   and save, then use it as the template. Do not guess the format.
4. Copy the template's text and change only: the asset name fields (`name`, and `%Name` when the template has
   it), paths that contain the old name, the `parent` folder if it should differ, and the type-specific content
   (event list, frames, code). Keep every `$Type` tag, `resourceType`, `resourceVersion`, key order, trailing
   commas and indentation exactly as the template has them.
5. Register the asset in the `.yyp` `resources` array by copying an existing entry of the same shape and editing
   name and path. Insert it in alphabetical position by name, like the IDE does. A `parent` folder must already
   exist in the `.yyp` `Folders` list — copy a folder entry to add a new one.
6. Run the checker (below), then read back every file written and confirm its content. Writes into synced or
   mounted folders can fail silently; a file that did not change looks exactly like a successful edit.

Details per asset type are in `references/asset-recipes.md`. Read it before creating sprites, rooms or collision
events.

## Editing safely

- Make minimal edits. Do not pretty-print, reformat, re-sort or "fix" trailing commas in `.yy`/`.yyp` files —
  GameMaker writes trailing commas itself and rewrites key order to its own liking; a reformatted file produces a
  huge diff and can be rejected.
- Event code lives in plain `.gml` files next to the object's `.yy` (`Create_0.gml`, `Step_0.gml`, …). Editing an
  existing event's `.gml` needs no `.yy` change. Adding a new event needs both the `.gml` file and an entry in the
  object's `eventList`, copied from an existing entry. File names and event numbers are in
  `references/event-files.md`.
- Ask whether the GameMaker IDE is open before writing. If it is, tell the user that when the IDE notices the
  change it must be **reloaded from disk**, never saved over — saving from the IDE discards everything written
  on disk. Safest is to close the project in the IDE first.
- Deleting or renaming an asset by hand touches the `.yyp`, the asset folder, room instance lists, parent
  references and every piece of GML that names it. Prefer asking the user to do renames and deletions in the IDE.
  If the working environment cannot delete files, leave the orphaned files in place: an unregistered folder is
  harmless, a registered folder with missing files is not.
- Rooms: prefer letting the user place instances and tiles in the Room Editor. Writing room `.yy` files by hand
  (instance lists, layer types, tilesets) is the most fragile edit in a project; do it only by copying from a room
  in the same project, and treat tilesets as IDE-only.

## Checking the project

Run the bundled checker after every batch of edits and before telling the user to open the project:

```bash
python3 <this skill's folder>/scripts/check_project.py <project folder or .yyp path>
```

It reads `.yy` files the way GameMaker writes them (trailing commas allowed) and reports:
- errors: unparseable files, registered assets whose files are missing, name/path mismatches, parents that point
  to folders the project does not list, event entries without their `.gml` file, duplicate asset names
- warnings: `.gml` event files no event entry uses, asset folders on disk the `.yyp` does not register, and any
  asset whose type tags or `resourceVersion` differ from the other assets of its type (the usual sign of a
  template copied from the wrong version)

Fix every error before handing back. Explain warnings in one line each. The checker uses only the Python
standard library. It cannot compile GML — the user has to run the game for that; ask them to paste the full error
text if it fails (see the `gml-code` skill for reading GameMaker error messages).

## Reporting back

Tell the user which assets were added or changed, which ones need their attention in the IDE (sprite origins,
collision masks, room placement), and whether the IDE needs a reload. Do not describe file paths unless asked.
