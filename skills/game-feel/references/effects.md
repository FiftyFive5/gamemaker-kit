# Effects

All snippets assume a persistent controller `obj_game` and initialise their variables in its Create.

## Screen shake (trauma model)

Trauma accumulates from events and decays; shake = trauma², which makes small hits subtle and big hits strong.

```gml
// obj_game Create
global.trauma = 0;
global.shake_scale = 1;          // 0 turns shake off (settings)
// helper (script)
function juice_shake(_amount) { global.trauma = min(1, global.trauma + _amount); }   // 0.2 small, 0.5 big
// camera End Step, after computing cx, cy
var s = global.trauma * global.trauma * 8 * global.shake_scale;   // max offset in pixels
cx += random_range(-s, s);
cy += random_range(-s, s);
global.trauma = max(0, global.trauma - 0.03);
```

If the project has no camera object, shake by moving the view: `camera_set_view_pos(view_camera[0], base_x + ox,
base_y + oy)`.

## Hit stop (freeze frames)

Freeze gameplay for a few frames on impact. Cheapest version: gameplay objects skip their Step while the counter
runs.

```gml
// obj_game Create
global.hitstop = 0;
// helper
function juice_hitstop(_frames) { global.hitstop = max(global.hitstop, _frames); }  // 3–6 normal, 8–12 big
// obj_game Begin Step
if (global.hitstop > 0) global.hitstop--;
// gameplay objects: first line of Step (combine with the pause check if the project has one)
if (global.hitstop > 0) exit;
```

Also set `image_speed = 0` on the involved objects during hit stop so animation freezes too, and restore after.

## Squash and stretch

```gml
// Create
draw_xscale = 1;
draw_yscale = 1;
// on landing / jumping / being hit
draw_xscale = 1.3; draw_yscale = 0.7;     // squash (landing)
// draw_xscale = 0.75; draw_yscale = 1.25; // stretch (jump)
// Step
draw_xscale = lerp(draw_xscale, 1, 0.2);
draw_yscale = lerp(draw_yscale, 1, 0.2);
// Draw
draw_sprite_ext(sprite_index, image_index, x, y, draw_xscale * facing, draw_yscale, image_angle, image_blend, image_alpha);
```

Keep the squash in separate variables (not `image_xscale`) so collision masks are not affected. Bottom-centred
sprite origins make squash look grounded.

## Hit flash

Draw the sprite solid white for a few frames using fog:

```gml
// Create
flash = 0;
// when hit
flash = 4;
// Step
flash = max(0, flash - 1);
// Draw
if (flash > 0) {
    gpu_set_fog(true, c_white, 0, 0);
    draw_self();
    gpu_set_fog(false, c_white, 0, 0);
} else draw_self();
```

## Particles

```gml
// obj_game Create
global.ps = part_system_create();
part_system_depth(global.ps, -100);

global.pt_dust = part_type_create();
part_type_shape(global.pt_dust, pt_shape_pixel);
part_type_size(global.pt_dust, 1, 2, -0.02, 0);
part_type_colour2(global.pt_dust, c_white, c_gray);
part_type_alpha2(global.pt_dust, 1, 0);
part_type_speed(global.pt_dust, 0.5, 1.5, -0.05, 0);
part_type_direction(global.pt_dust, 0, 360, 0, 0);
part_type_life(global.pt_dust, 15, 30);

// helper
function juice_burst(_x, _y, _type, _count) { part_particles_create(global.ps, _x, _y, _type, _count); }

// obj_game Clean Up
part_type_destroy(global.pt_dust);
part_system_destroy(global.ps);
```

- Create particle types once (controller Create), never every step — each `part_type_create` allocates.
- Recent GameMaker versions also have a Particle System asset editor; if the project uses particle assets,
  create them with `part_system_create(ps_asset)` instead.
- Sprites as particles: `part_type_sprite(type, spr, animate, stretch, random)`.

## Floating text

```gml
// obj_float_text Create (spawn with a variable struct so Create sees the values)
if (!variable_instance_exists(id, "text")) text = "";   // normally passed in via the struct
vy = -1;
life = 40;
// Step
y += vy; vy *= 0.95; life--;
if (life <= 0) instance_destroy();
// Draw
draw_set_halign(fa_center);
draw_set_alpha(min(1, life / 15));
draw_text(x, y, text);
draw_set_alpha(1);
draw_set_halign(fa_left);

// spawning
instance_create_depth(x, y - 16, -200, obj_float_text, { text: "+10$" });
```

The variable struct is applied before Create runs, so Create only fills in a default when no text was passed.

## Easing

`lerp(a, b, 0.2)` each step gives an ease-out that never fully arrives — snap when close
(`if (abs(a - b) < 0.01) a = b;`). For timed tweens use a 0–1 progress value and an ease function:

```gml
function ease_out_back(_t) { var c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * power(_t - 1, 3) + c1 * power(_t - 1, 2); }
// t goes 0 → 1 over N frames; scale = ease_out_back(t);
```

Recent versions also offer Animation Curve assets (`animcurve_get_channel`, `animcurve_channel_evaluate`) for
designer-tweakable curves.

## Putting it together: a big hit

```gml
// inside the thing that got hit
flash = 5;
draw_xscale = 1.35; draw_yscale = 0.7;
juice_hitstop(6);
juice_shake(0.4);
juice_burst(x, y, global.pt_dust, 12);
sfx(snd_hit, 0.15);
instance_create_depth(x, y - 20, -200, obj_float_text, { text: "BONK" });
```

Tune by halving and doubling each value in a playtest rather than guessing in code.
