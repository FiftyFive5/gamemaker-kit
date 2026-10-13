# Asset recipes

Every recipe starts the same way: copy a same-type asset from this project (see SKILL.md). These notes say what
to change and what to watch for. Names are examples.

## Object

Files: `objects/obj_enemy/obj_enemy.yy` plus one `.gml` per event.

Change in the copied `.yy`: `name` (and `%Name` if present), `eventList` (copy entries, edit numbers), `parent`
folder, `spriteId` (a reference to a sprite in the same shape the template uses, or `null`), `parentObjectId`
for inheritance, `persistent`, `visible`, `solid`. Keep `properties`/`overriddenProperties` as an empty list
unless the template's object uses them.

Register: one `resources` entry in the `.yyp`.

Give a new object a sprite reference whenever one exists — objects without sprites are invisible in the Room
Editor, which makes them hard for the user to place.

## Script

Files: `scripts/scr_math/scr_math.yy` and `scripts/scr_math/scr_math.gml`.

Since GameMaker 2.3 a script asset is a file of function declarations that run once at game start; it is not
itself a callable function. Put `function name(args) { ... }` declarations inside. The asset name and the
function names may differ.

## Sprite

Sprites are the most involved asset. A sprite folder normally holds:

- `sprites/spr_x/spr_x.yy` with a frames list, a layers list and a `sequence` block (timeline, playback speed)
- one composite PNG per frame named after the frame's id
- one PNG per frame per layer under `layers/<frame id>/<layer id>.png`

Recipe:
1. Copy an existing sprite from the project with the same number of layers (normally 1). Prefer one with the
   same frame count.
2. Generate fresh unique ids (UUIDs, in the same textual format the template uses) for every frame and for the
   layer, and replace every occurrence of each old id consistently — ids appear in the frames list, the sequence
   keyframes and the file/folder names.
3. Write each frame image twice: as the composite PNG and as the layer PNG, both at the size set in the `.yy`
   (`width`, `height`). All frames must share that size.
4. Set the bounding box (`bbox_left/right/top/bottom`), origin (`origin` preset and `sequence.xorigin/yorigin`)
   to sensible values, then tell the user to check origin and collision mask in the Sprite Editor.
5. Update frame count and length in the sequence the same way the template expresses them.

When importing a sprite strip or sheet, slice it into frames with Python (Pillow) before writing. If more than a
few sprites are needed, write one, have the user open the project to confirm it loads, then do the rest.

## Sound, font, path, tileset, sequence

Same rule: copy from the project. Sounds also need their audio file beside the `.yy`; fonts carry a generated
glyph texture the IDE regenerates — prefer creating fonts and tilesets in the IDE.

## Room

Rooms hold layer lists, instance lists (each instance with its own id), creation order and per-instance
overrides. Prefer instructing the user to place things in the Room Editor. If an edit is unavoidable, copy an
instance entry from the same room, give it a new unique name in the format the room already uses, and add it to
both the layer's instance list and the room's creation-order list if the room has one.

## Folders

In the `.yyp`, the `Folders` list defines the asset browser tree; an asset's `parent` must reference one of its
paths. Copy an existing folder entry to add one.

## Making the game build instead of the project

When an asset can be avoided by doing something in code (spawning instances from a controller object, drawing
UI with draw functions, reading data from an included JSON file), that is often more robust than generating
assets by hand. Offer it when the user's goal allows.
