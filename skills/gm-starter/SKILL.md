---
name: gm-starter
description: >
  This skill should be used when the user wants to get a GameMaker game playable fast or add ready-made
  systems: "start a new game", "make me a prototype", "set up a starter project", "I have an empty
  GameMaker project", "add a camera/input/save/pause system", "two players on one keyboard quickly",
  "make levels with text", "ASCII level", "design levels without the room editor", "level from a map string".
metadata:
  version: "0.1.0"
---

# Starter kit and drop-in systems

The scaffolding script installs a playable game or individual systems into an existing GameMaker project,
cloning the project's own file formats like every other `gm.py` command. Scripts live in the
`gamemaker-assets` skill: `<plugin>/skills/gamemaker-assets/scripts/gm.py`.

## A playable game in one command

```bash
python3 gm.py starter <project> --genre topdown      # or --genre platformer
```

Adds: `obj_game` (persistent controller), `obj_player`, `obj_wall`, `obj_camera`, `obj_fade`,
`obj_float_text`, placeholder sprites `spr_player`/`spr_wall`, and scripts `scr_input`, `scr_juice`,
`scr_save`, `scr_level`, `scr_transition`. The level is ASCII text in `scr_level`.

What the user gets after the one manual step (dragging `obj_game` into the first room):
- two players on one keyboard (WASD + E, arrows + L); gamepads join automatically and pause on disconnect
- a camera that frames both players, zooms out when they spread, clamps to the level, and shakes
- the action button demos the juice: squash, flash, particles, shake, floating "BONK!" text, money counter
- platformer genre: coyote time, jump buffer, variable jump height, landing dust
- Esc/Start pause with audio pause, Ctrl+R restart, settings saved to JSON

Requirements and refusals:
- The project needs at least one object **with an event** and one script, plus one sprite, so formats can be
  copied. In a brand-new project, ask the user to create one object with a Create event, one script and one
  sprite in the IDE first (any content), then run.
- If any of the kit's names already exist, the script refuses and lists them. Re-run with `--prefix kit_`
  (asset names get the prefix; GML references are rewritten). Function names (`input_init`, `juice_shake`…)
  are not prefixed — if the project already defines them, install only the missing systems.
- Needs Pillow for the placeholder sprites.

Tell the user plainly: **drag `obj_game` into the first room in the IDE, then run.** That is the only manual
step; everything else is spawned from the text level.

## Individual systems

```bash
python3 gm.py add-system <project> input juice save level camera fade
```

| System | Adds | Wire-up the user (or Claude) must add |
|---|---|---|
| input | `scr_input` | `input_init(<players>)` in the controller's Create |
| juice | `scr_juice`, `obj_float_text` | `juice_init()` in Create, `juice_cleanup()` in Clean Up; gameplay Steps start with `if (global.hitstop > 0) exit;` |
| save | `scr_save` | `settings_load()` in Create; `save_struct`/`load_struct` anywhere |
| level | `scr_level` | `level_build_for_room()` in the controller's Room Start |
| camera | `obj_camera` (+ juice, level) | in Room Start: create it if missing, then `with (obj_camera) camera_setup();` |
| fade | `obj_fade`, `scr_transition` | `fade_to_room(rm_next)` |

After `add-system`, make those wire-up edits in the project's existing controller rather than adding a second
controller.

## Text levels

```gml
// scr_level (or any script's top level)
level_legend_set("#", obj_wall);
level_legend_set("M", obj_monkey);
level_legend_set("P", obj_player, { player_index: 0 });
global.levels[$ "rm_zoo"] = [
    "##########",
    "#P....M..#",
    "#..####..#",
    "##########",
];
```

- One character = one cell (`global.level_cell`, 16 px by default); instances are created at cell centres
  with `instance_create_depth`, and the struct is applied before their Create runs.
- `global.levels[$ "default"]` is used for rooms without their own level — remove it once real rooms have
  levels, or every room gets the default map.
- `global.level_w` / `global.level_h` hold the level size; the kit's camera clamps to it.
- Designing levels is now a text edit: offer to draft several level variants from the user's description
  (e.g. "a zoo with three pens and a lake in the middle") and paste them into `scr_level`.

Review generated GML with the `gml-reviewer` agent when the user changes it substantially, and run
`check_project.py` after installing.
