---
name: local-coop-input
description: >
  This skill should be used when a GameMaker game needs local multiplayer or flexible input: "add a second
  player", "co-op on one keyboard", "gamepad support", "controller connect/disconnect", "rebind keys",
  "remap controls", "shared camera for two players", "split screen", "which player is which controller", or
  when input code is hard-wired to specific keys in many objects.
metadata:
  version: "0.1.0"
---

# Local co-op and input

## Principle: actions, not keys

Gameplay code asks "did player 2 press *action*?", never "is `L` pressed?". One input layer maps devices to
players and keys/buttons to actions. Then adding a gamepad, a third player or rebinding touches one place.

```
devices (keyboard sides, gamepads) → bindings per player → actions (move_x, move_y, action, drop, aim…) → objects
```

## Steps

1. Read how the project reads input today (grep for `keyboard_check`, `gamepad_`, `mouse_check`). List every
   action the game uses.
2. Add the input layer from `references/input-layer.md`: one `input_*` script with a per-player binding table and
   `input_axis(player, ...)`, `input_pressed(player, action)`, `input_held(player, action)`.
3. Replace direct key checks in objects with the layer's functions, one object at a time. Each player object
   gets a `player_index` (0, 1, …) set at creation (pass it in the variable struct so Create sees it).
4. Handle gamepad hot-plugging in the controller's Async – System event (see reference).
5. Pick a camera: shared camera that frames all players (default for co-op chaos games) or split screen.
6. Store bindings in the save file's settings section if rebinding is offered.

## Defaults that avoid common co-op complaints

- Two players on one keyboard: WASD + one action key on the left, arrows + one action key on the right, keys far
  enough apart that hands do not collide. Avoid modifier keys (Shift/Ctrl/Alt) — some keyboards cannot register
  them together with other keys (ghosting).
- A gamepad that connects joins the lowest free player slot; one that disconnects pauses the game rather than
  removing the player.
- Apply a stick dead zone (`gamepad_set_axis_deadzone(slot, 0.25)`), and normalise diagonal movement.
- Player identity must be readable at a glance: distinct colours/outlines, an indicator above each player when
  they overlap or leave the screen.
- Friendly interactions (throwing, stunning each other) should have a short immunity window so one player cannot
  lock another out.

For mature projects, the free open-source **Input** library for GameMaker (by Juju Adams and contributors) covers
rebinding, hot-plugging and many controller types; suggest it when the user needs more than the reference layer
offers, and let them install it from its official release page.

Code for the input layer, hot-plugging, shared camera and split screen: `references/input-layer.md`.
