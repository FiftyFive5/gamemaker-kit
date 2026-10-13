---
name: gm-performance
description: >
  This skill should be used when a GameMaker game runs slowly or misbehaves over time: "the game lags",
  "FPS drops", "stutters when many enemies spawn", "memory keeps growing", "memory leak", "how do I use the
  debugger/profiler", "texture pages", "texture swaps", "game freezes for a moment", or when preparing a build
  for weaker hardware (Steam Deck, old laptops).
metadata:
  version: "0.1.0"
---

# Performance and debugging in GameMaker

Measure before changing code. Most GameMaker slowdowns come from a handful of causes, and the debugger shows
which one within a minute.

## 1. Measure

- Run with the **Debug** button (or F6) instead of Run. The debugger shows the profiler (time per event and
  function), instance counts, variables, memory and watches. Turn the profiler on, play the slow moment, then
  sort by total time.
- In-game numbers: `fps` is capped at the game speed; `fps_real` is how many frames the game *could* do —
  watch that one. `show_debug_overlay(true)` toggles the built-in overlay; recent versions add `dbg_view`,
  `dbg_slider` etc. for custom debug panels.
- Memory over time: watch the memory graph in the debugger while playing several rounds. A line that only goes
  up across rounds is a leak.
- Ask the user for the profiler's top entries (event name + time) when they run it; do not guess from code alone
  when numbers are available.

## 2. Usual causes, in order of likelihood

| Symptom | Likely cause | Fix |
|---|---|---|
| Slower as more instances exist | Every instance runs Step code that loops over all others (`with (obj_enemy)` inside an enemy, `instance_nearest` every step) | Cache targets, update expensive searches every N frames, use a manager object that loops once |
| Many objects off-screen still updating | Large rooms | `instance_deactivate_region` / `instance_activate_region` around the camera each few frames (keep important objects active) |
| Draw-heavy slowdowns | Many texture swaps between texture pages | Put sprites drawn together in the same **texture group** (IDE: Texture Groups), draw tiles via tile layers, avoid switching blend modes/shaders per instance |
| Memory grows every round | `ds_*` structures, surfaces, buffers, particle systems, cameras created and never destroyed | Destroy in Clean Up: `ds_list_destroy`, `surface_free`, `buffer_delete`, `part_system_destroy`, `camera_destroy`; structs and arrays are garbage-collected, these are not |
| Short freeze the first time something appears | Texture page loaded on first use | Pre-fetch texture groups during a loading moment (`texture_prefetch`, or `texturegroup_load` in recent versions) |
| Freeze on room change | Huge rooms with many instances created at once | Spread creation over frames or reduce instance counts with tile layers |
| Random spikes | `show_debug_message` spam, string building every step, file I/O during play | Remove logging in hot code, cache strings, save at safe moments |
| CPU-bound logic | Heavy GML in the VM | Build with **YYC** for release (needs the YYC compiler set up) — often several times faster for logic |

## 3. Code habits that keep it fast

- Collision functions are cheap for single checks but add up: check `place_meeting` against the object you need,
  not `all`; use `collision_*_list` once rather than many single checks.
- Avoid creating and destroying hundreds of instances per second for bullets/particles; use the particle system
  for visual-only effects.
- Tilemaps for walls and floors instead of one instance per tile; check walls with an invisible wall object or
  `tilemap_get_at_pixel`.
- Do not call `instance_number`, `instance_find` in loops every step on large counts.
- Draw GUI text with a font set once; avoid `draw_text_transformed` for hundreds of labels.

## 4. Debugging behaviour bugs

- Reproduce first: ask for exact steps, then add `show_debug_message` with frame number (`current_time` or a
  counter) at the suspicious points, or a breakpoint in the debugger.
- For "it works sometimes": suspect event order between instances (see `gml-code` trap 5) and variables
  assigned after creation (trap 4).
- Read the full error message: the `gml_Object_<obj>_<Event>_<n> (line N)` part names the file and line.

Report findings to the user as: measured cause → change → expected effect → how to verify (e.g. "fps_real in
the 3-minute round should stay above 200 instead of dropping to 60").
