# Core recipes: state machine and movement

## State machine

Each state is a method stored on the instance; `state_enter` runs once on every change.

```gml
// Create
hp = 3;
move_speed = 1.5;
target = noone;
state_timer = 0;

state_idle = function() {
    target = instance_nearest(x, y, obj_player);
    if (target != noone && point_distance(x, y, target.x, target.y) < 120) change_state(state_chase);
};
state_chase = function() {
    if (!instance_exists(target)) { change_state(state_idle); exit; }
    var dir = point_direction(x, y, target.x, target.y);
    move_and_collide(lengthdir_x(move_speed, dir), lengthdir_y(move_speed, dir), obj_wall);
    if (point_distance(x, y, target.x, target.y) > 200) change_state(state_idle);
};
state_stunned = function() {
    if (state_timer > 90) change_state(state_idle);
};

change_state = function(_new) {
    state = _new;
    state_timer = 0;
};
state = state_idle;

// Step
state_timer++;
state();
```

Notes:
- `move_and_collide(dx, dy, obj)` moves while sliding along instances of `obj` and returns an array of the
  instances it hit. It exists in recent GameMaker versions only; if the project's IDE reports it as unknown, use
  the axis-by-axis loop from Top-down movement.
- Compare states with `state == state_stunned`. Expose a readable name for debugging if needed
  (`state_name = "chase"` inside `change_state`).
- `exit` leaves the current event or function.

## Top-down movement

```gml
// Create
walk_speed = 2;
hsp = 0;
vsp = 0;

// Step
var ix = (keyboard_check(ord("D")) || keyboard_check(vk_right)) - (keyboard_check(ord("A")) || keyboard_check(vk_left));
var iy = (keyboard_check(ord("S")) || keyboard_check(vk_down))  - (keyboard_check(ord("W")) || keyboard_check(vk_up));
if (ix != 0 || iy != 0) {
    var dir = point_direction(0, 0, ix, iy);   // normalises diagonals
    hsp = lengthdir_x(walk_speed, dir);
    vsp = lengthdir_y(walk_speed, dir);
} else {
    hsp = 0;
    vsp = 0;
}

// Collide one axis at a time
if (place_meeting(x + hsp, y, obj_wall)) {
    while (!place_meeting(x + sign(hsp), y, obj_wall)) x += sign(hsp);
    hsp = 0;
}
x += hsp;
if (place_meeting(x, y + vsp, obj_wall)) {
    while (!place_meeting(x, y + sign(vsp), obj_wall)) y += sign(vsp);
    vsp = 0;
}
y += vsp;
```

Facing for 4-direction sprites: keep the last non-zero input direction in a variable and pick the sprite from
it. Requires the object to have a sprite or collision mask; the wall object too.

Acceleration and friction instead of instant speed:

```gml
var accel = 0.4, fric = 0.3;
hsp = (ix != 0) ? clamp(hsp + ix * accel, -walk_speed, walk_speed) : max(abs(hsp) - fric, 0) * sign(hsp);
```

## Platformer movement

```gml
// Create
run_speed = 2.5;
jump_speed = 5.5;
grav = 0.3;
max_fall = 7;
hsp = 0;
vsp = 0;
coyote = 0;          // frames since leaving the ground
jump_buffer = 0;     // frames since jump was pressed
COYOTE_FRAMES = 6;
BUFFER_FRAMES = 6;

// Step
var ix = keyboard_check(vk_right) - keyboard_check(vk_left);
hsp = ix * run_speed;

var on_ground = place_meeting(x, y + 1, obj_wall);
coyote = on_ground ? 0 : coyote + 1;
jump_buffer = keyboard_check_pressed(vk_space) ? 0 : jump_buffer + 1;

if (jump_buffer <= BUFFER_FRAMES && coyote <= COYOTE_FRAMES) {
    vsp = -jump_speed;
    jump_buffer = BUFFER_FRAMES + 1;
    coyote = COYOTE_FRAMES + 1;
}
// variable jump height: release early to cut the jump
if (vsp < 0 && !keyboard_check(vk_space)) vsp = max(vsp, -jump_speed * 0.4);

vsp = min(vsp + grav, max_fall);

if (place_meeting(x + hsp, y, obj_wall)) {
    while (!place_meeting(x + sign(hsp), y, obj_wall)) x += sign(hsp);
    hsp = 0;
}
x += hsp;
if (place_meeting(x, y + vsp, obj_wall)) {
    while (!place_meeting(x, y + sign(vsp), obj_wall)) y += sign(vsp);
    vsp = 0;
}
y += vsp;
```

Use sub-pixel-safe positions if the art is pixel-perfect: keep `x`/`y` fractional and draw at
`floor(x)`, `floor(y)`, or round speeds to whole pixels.

## Knockback

```gml
// on hit (inside the victim)
var dir = point_direction(other.x, other.y, x, y);
kb_x = lengthdir_x(4, dir);
kb_y = lengthdir_y(4, dir);
// Step: apply and decay
hsp += kb_x;  vsp += kb_y;
kb_x *= 0.8;  kb_y *= 0.8;
if (abs(kb_x) < 0.1) kb_x = 0;
if (abs(kb_y) < 0.1) kb_y = 0;
```

Initialise `kb_x = 0; kb_y = 0;` in Create.
