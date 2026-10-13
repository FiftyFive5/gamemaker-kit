---
name: gml-systems
description: >
  This skill should be used when Claude builds a common game system in GameMaker: "add a state machine",
  "make the player move", "top-down movement", "platformer jump", "wall collision", "camera that follows the
  player", "save and load", "save file", "music and sound manager", "pause menu", "fade between rooms",
  "room transition", "game manager object". It provides proven GML patterns to adapt to the project.
metadata:
  version: "0.1.0"
---

# Common GameMaker systems

Patterns for the systems most games need. They are starting points: read the project first and adapt names,
input handling and structure to what is already there. Never paste a pattern that duplicates a system the
project already has — extend the existing one.

## Picking a recipe

| Need | Read |
|---|---|
| Enemy/player behaviour with distinct modes (idle, chase, stunned…) | `references/core.md` → State machine |
| Top-down 4/8-direction movement with walls | `references/core.md` → Top-down movement |
| Platformer run/jump with coyote time and jump buffer | `references/core.md` → Platformer movement |
| A camera that follows, stays in the room, can shake and zoom | `references/world.md` → Camera |
| Saving progress and settings | `references/world.md` → Save and load |
| Music, sound effects, volume settings | `references/world.md` → Audio |
| Pause menu | `references/world.md` → Pause |
| Fading between rooms | `references/world.md` → Room transitions |

## Architecture defaults

- One persistent controller object (`obj_game`) placed in the first room owns global state: score, money,
  pause flag, settings, the save/load functions' entry points. Systems that must survive room changes
  (camera, music, transitions) are either this object or their own persistent objects created once.
- Global helper functions go in script assets (functions declared at a script's top level are global).
- Per-object behaviour goes in the object's events; shared behaviour goes in a parent object whose children call
  `event_inherited()`.
- Initialise every variable in Create. Read input once per step into variables (`input_left`, `input_jump`) and
  use those, so input can later be swapped for gamepads or other players (see `local-coop-input`).

## Methods inside objects

Functions assigned to instance variables in Create are bound to the instance:

```gml
// Create
state_idle = function() { /* runs as this instance */ };
state = state_idle;
// Step
state();
```

A function written inside a struct literal (`states = { idle: function() {…} }`) is bound to the **struct**, not
the instance — `x`, `y` and other instance variables are not reachable as plain names there. Use the
instance-variable form above, or wrap with `method(id, function() {…})`.

## After adding a system

Tell the user which objects to place in which room (controllers usually go in the first room only, and must be
persistent if they should live across rooms), which events were added, and one concrete thing to test.
