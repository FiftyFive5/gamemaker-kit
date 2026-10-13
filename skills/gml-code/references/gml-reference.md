# GML reference notes

Facts that commonly trip up generated code. When the project's code does something differently and it works,
follow the project.

## Variables and scope

- Plain assignment in an object event creates an **instance** variable. `var name = …` creates a **local** that
  lives until the event or function ends; locals are visible inside `with` blocks in the same event.
- `global.name` is game-wide. `static name = …` inside a function keeps its value between calls.
- Variable names: letters, digits, underscores, starting with a letter or underscore, up to 64 characters, and
  not the same as an asset name. Chained assignment (`a = b = 0;`) is not allowed.
- Reading a variable nobody assigned yet is a runtime error ("not set before reading it"). Initialise in Create;
  use `variable_instance_exists(id, "name")` only when a variable is genuinely optional.

## Functions, methods and structs

- `function f(a, b = 1) { … }` declares a function. Inside an object event or a constructor it becomes a method
  bound to that instance/struct; in a script asset it is a global function.
- Structs: `var s = { hp: 3, name: "lion" };` — access with `s.hp`. Constructors: `function Enemy(_hp)
  constructor { hp = _hp; }` and `new Enemy(5)`.
- `method(instance_or_struct, func)` binds a function to a scope, for callbacks that must run as a specific
  instance.
- Structs and arrays are references: assigning one to another variable does not copy it. Use `variable_clone`
  (recent versions) or build a new struct/array when a copy is needed.

## Arrays

- `array_length(a)`, `array_push(a, v)`, `array_delete(a, index, count)`, `array_contains(a, v)`,
  `array_foreach`, `array_sort`. Loop with `for (var i = 0; i < array_length(a); i++)`.
- Deleting while iterating forward skips elements; iterate backwards when deleting.

## Instances

- `instance_exists(obj_or_id)` before using an id that may have been destroyed. A destroyed instance's id stays in
  variables that held it.
- `instance_number(obj)`, `instance_find(obj, n)`, `instance_nearest(x, y, obj)`.
- `noone` is the "no instance" value returned by lookups; compare with `!= noone`.

## Collisions

- `place_meeting(x, y, obj)` → true/false at a hypothetical position; `instance_place(x, y, obj)` → the instance
  or `noone`. Both use the calling instance's collision mask, so an object without a sprite or mask never
  collides.
- `collision_circle`, `collision_rectangle`, `collision_line`, `collision_point` test shapes and return an
  instance or `noone`; the `_list` variants collect all hits.
- For tile-based walls, check against a dedicated invisible wall object or the tilemap
  (`tilemap_get_at_pixel`), not visual tiles.
- Standard pixel-safe movement: move one axis at a time; if `place_meeting(x + hsp, y, obj_wall)`, step
  `sign(hsp)` until touching, then set `hsp = 0`; repeat for y.

## Randomness

- The random seed is the same every run until `randomize()` is called (once, e.g. in the first controller's
  Create). `irandom(n)` includes n; `random(n)` does not.

## Drawing

- Draw functions only work inside Draw events. Colour and alpha set with `draw_set_colour`/`draw_set_alpha`
  stay set for later draws — reset them after use.
- `draw_text` uses the current font (`draw_set_font`); set alignment with `draw_set_halign`/`draw_set_valign` and
  reset it.
- Surfaces can be lost (e.g. when the window changes); check `surface_exists` before every use and recreate.

## Input

- `keyboard_check` (held), `keyboard_check_pressed` (this step only), `keyboard_check_released`.
- Gamepads: `gamepad_is_connected(slot)`, `gamepad_button_check_pressed(slot, gp_face1)`,
  `gamepad_axis_value(slot, gp_axislh)`; apply a dead zone (`gamepad_set_axis_deadzone`).

## Debugging

- `show_debug_message(string)` prints to the IDE output window. String concatenation needs `string(value)` for
  numbers in older code; recent versions also support template strings: `$"hp = {hp}"`.
- The error line `at gml_Object_<object>_<Event>_<num> (line N)` names the exact file and line:
  `gml_Object_obj_enemy_Step_0` → `objects/obj_enemy/Step_0.gml`. `gml_Script_<name>` points into a script asset.
