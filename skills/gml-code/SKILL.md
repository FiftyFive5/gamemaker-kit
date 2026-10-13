---
name: gml-code
description: >
  This skill should be used when Claude writes, reviews or debugs GML (GameMaker Language) code: "write the
  enemy AI", "make the player jump", "why does this variable not change", "fix this GameMaker error",
  "ERROR in action number 1 of Step Event", "not set before reading it", "my with() block does nothing",
  "the draw order is wrong", or any change to .gml event, script or function code in a GameMaker project.
metadata:
  version: "0.1.0"
---

# Writing GML that works the first time

Claude cannot run GameMaker in its own environment, so the user is the compiler. Every round trip costs them a
build. Prefer code that is obviously correct over clever code, check the traps below before handing code over,
and say what to look for when they run it.

## Before writing

- Read the object's existing events first. Variables an event reads must be initialised in Create (or in the
  parent's Create if the object inherits — and then the child's Create must call `event_inherited()`).
- Match the project's style: naming prefixes (`obj_`, `spr_`, `scr_`), whether it uses structs or ds_ structures,
  how input is read, where global state lives.
- Check names against assets: a variable may not share a name with an asset (object, sprite, script function…).

## The traps (check every one before handing code back)

1. **`with` flips the scope.** Inside `with (target) { … }`, plain names and `self` are the *target's*; `other` is
   the instance that ran the `with`. To change the caller's variable from inside, write `other.var = …`. A plain
   `on_ice = true` inside `with (obj_player)` sets the player's variable, not the caller's. Local `var`
   variables declared before the `with` stay readable and writable inside it.
2. **`with (obj_x)` runs for every instance** of `obj_x` and its children — and for none if there are none.
   Use an instance id (`with (inst)`) when one instance is meant.
3. **Object-name dot access:** `obj_enemy.hp -= 1` changes all enemies; reading `obj_enemy.hp` gives one
   arbitrary instance's value. Use instance ids from `instance_place`, `instance_nearest`, `collision_*`
   functions or the value returned by `instance_create_*`.
4. **Create runs immediately.** `instance_create_layer`/`instance_create_depth` run the new instance's Create
   event before returning, so variables assigned on the returned id afterwards are not visible inside Create.
   Pass them in the optional variable struct argument (`instance_create_layer(x, y, layer, obj, { move_speed: 4 })`),
   which is applied before Create runs — and make sure Create does not then overwrite them with a default
   (`if (!variable_instance_exists(id, "move_speed")) move_speed = 2;` keeps a passed value). Otherwise set them after creation and use them only from Step on.
5. **Order is not guaranteed between instances.** Within one event, which instance runs first is unspecified.
   If B must see A's update from this frame, move one side to Begin Step or End Step. Order per frame is
   Begin Step → Step → End Step → Draw Begin → Draw → Draw End → Draw GUI.
6. **A Draw event replaces default drawing.** Once an object has a Draw event, its sprite is no longer drawn
   automatically — call `draw_self()` (or `draw_sprite_ext`) yourself.
7. **Draw GUI is in screen space.** Coordinates in Draw GUI are relative to the GUI layer, not the room or the
   camera. HUDs belong there; world objects do not.
8. **Depth sorting.** For top-down y-sorting set `depth = -y` each Step (or Begin Step); be aware that assigning
   `depth` moves the instance off its room layer into a managed layer.
9. **Alarms count frames** and fire when they reach 0; `-1` means off. An alarm with no Alarm event does nothing.
10. **Frame-based vs time-based.** Speeds written per step depend on the game speed
    (`game_get_speed(gamespeed_fps)`); use `delta_time` (microseconds) only if the project already does.
11. **Destroy during iteration.** Destroying instances inside `with` is fine, but code after `instance_destroy()`
    in the same event still runs for that instance.
12. **Globals:** `global.x` must be assigned before any read, usually in a controller's Create or a script's
    top-level code (script top-level code runs once at game start, before the first room).

More on structs, methods, arrays, collisions and error messages: `references/gml-reference.md`.

## Reading GameMaker errors

A runtime error looks like:

```
ERROR in action number 1
of Step Event0 for object obj_enemy:
Variable obj_enemy.target(100012, -2147483648) not set before reading it.
 at gml_Object_obj_enemy_Step_0 (line 14) - if (target.hp <= 0)
```

Read it as: object `obj_enemy`, event Step (`Step_0.gml`), line 14, variable `target` was read before any event
of that instance assigned it. The fix is almost always an initial value in Create, or a guard
(`if (instance_exists(target))`). Ask the user for the full text, including the `at gml_…` line; the first
line alone is rarely enough.

## Handing code back

Say which events changed, which variables were added to Create, and one concrete thing to test in-game ("hit
the monkey with the net twice; the second hit should stun it"). If an asset (new object, event or sprite) is
needed, follow the `gamemaker-assets` skill for creating it.
