# World recipes: camera, save/load, audio, pause, transitions

## Camera

A persistent `obj_camera` that follows a target, stays inside the room and supports shake.

```gml
// Create
view_w = 320;
view_h = 180;
follow = obj_player;          // object or instance
smooth = 0.15;                // 1 = locked, lower = softer
shake = 0;                    // set from anywhere: obj_camera.shake = 6;
cam = view_camera[0];

// Room Start (Other_4): views must be enabled in every room the camera works in
view_enabled = true;
view_visible[0] = true;
camera_set_view_size(cam, view_w, view_h);
if (instance_exists(follow)) { x = follow.x; y = follow.y; }

// End Step (runs after everything moved this frame)
if (instance_exists(follow)) {
    x = lerp(x, follow.x, smooth);
    y = lerp(y, follow.y, smooth);
}
var cx = clamp(x - view_w / 2, 0, max(0, room_width - view_w));
var cy = clamp(y - view_h / 2, 0, max(0, room_height - view_h));
cx += random_range(-shake, shake);
cy += random_range(-shake, shake);
shake = max(0, shake - 0.5);
camera_set_view_pos(cam, cx, cy);
```

- Window size and scaling: set the viewport (`view_wport[0]`, `view_hport[0]`) to a whole multiple of the view
  size for pixel art, and `window_set_size` / `surface_resize(application_surface, …)` to match.
- Zoom: change `view_w`/`view_h` together (keeping aspect ratio) and call `camera_set_view_size` each step.
- For pixel art, floor the final camera position (`floor(cx)`) to avoid shimmering.

## Save and load

Store a struct as JSON. Files written with these functions land in the game's sandboxed save folder
(per-user app data on desktop), not next to the project.

```gml
// script scr_save
#macro SAVE_FILE "save.json"

function save_game() {
    var data = {
        version: 1,
        money: global.money,
        unlocked: global.unlocked,              // arrays and structs nest fine
        settings: { music: global.vol_music, sfx: global.vol_sfx },
    };
    var json = json_stringify(data);
    var buf = buffer_create(string_byte_length(json) + 1, buffer_fixed, 1);
    buffer_write(buf, buffer_string, json);
    buffer_save(buf, SAVE_FILE);
    buffer_delete(buf);
}

function load_game() {
    if (!file_exists(SAVE_FILE)) return false;
    var buf = buffer_load(SAVE_FILE);
    var json = buffer_read(buf, buffer_string);
    buffer_delete(buf);
    var data;
    try { data = json_parse(json); } catch (e) { show_debug_message("bad save: " + string(e)); return false; }
    global.money    = data[$ "money"] ?? 0;          // tolerate missing keys from older saves
    global.unlocked = data[$ "unlocked"] ?? [];
    var s = data[$ "settings"] ?? {};
    global.vol_music = s[$ "music"] ?? 1;
    global.vol_sfx   = s[$ "sfx"] ?? 1;
    return true;
}
```

- Keep a `version` field and read every key with a default, so saves from older builds still load.
- Saving instances: store `object_get_name(object_index)`, position and the variables that matter; on load
  recreate with `instance_create_layer(x, y, layer_name, asset_get_index(name))`.
- Never store instance ids in a save — they change every run.
- Write saves at safe moments (end of round, settings menu close), not every step.

## Audio

```gml
// obj_game Create: set group gains once (audio groups are created in the IDE's Audio Groups settings)
global.vol_music = 1;
global.vol_sfx = 1;
music_playing = noone;

// helper script
function sfx(_snd, _pitch_var = 0.1) {
    var inst = audio_play_sound(_snd, 10, false);
    audio_sound_pitch(inst, 1 + random_range(-_pitch_var, _pitch_var));
    audio_sound_gain(inst, global.vol_sfx, 0);
    return inst;
}

function music(_snd, _fade_ms = 800) {
    with (obj_game) {
        if (music_playing != noone && audio_is_playing(music_playing)) {
            if (audio_sound_get_asset(music_playing) == _snd) exit;    // already playing
            audio_sound_gain(music_playing, 0, _fade_ms);
            // stop it later, e.g. with an alarm, once the fade has finished
        }
        music_playing = audio_play_sound(_snd, 100, true);
        audio_sound_gain(music_playing, 0, 0);
        audio_sound_gain(music_playing, global.vol_music, _fade_ms);
    }
}
```

- Slight random pitch on repeated sounds (footsteps, hits) avoids the "machine gun" effect.
- Limit simultaneous copies of the same sound: check `audio_is_playing(_snd)` or count instances before playing.
- If the project uses audio groups, set volumes with `audio_group_set_gain(group, value, 0)` instead of per sound.
- `audio_sound_get_asset` exists in recent versions; on older ones, remember the asset in a separate variable.

## Pause

Simplest robust approach: a global flag every gameplay object respects.

```gml
// obj_game Create
global.paused = false;
// obj_game Step
if (keyboard_check_pressed(vk_escape)) global.paused = !global.paused;
// gameplay objects, first line of Step / Begin Step / End Step
if (global.paused) exit;
// obj_game Draw GUI
if (global.paused) {
    draw_set_alpha(0.6); draw_set_colour(c_black);
    draw_rectangle(0, 0, display_get_gui_width(), display_get_gui_height(), false);
    draw_set_alpha(1); draw_set_colour(c_white);
    draw_set_halign(fa_center);
    draw_text(display_get_gui_width() / 2, display_get_gui_height() / 2, "PAUSED");
    draw_set_halign(fa_left);
}
```

Also stop what runs without Step code: set `image_speed = 0` while paused (or `global.paused ? 0 : 1`),
pause alarms by not decrementing your own timers, and pause sounds with `audio_pause_all()` /
`audio_resume_all()`. The alternative — `instance_deactivate_all(true)` — also stops drawing, so it needs a
captured screenshot (`sprite_create_from_surface(application_surface, …)`) drawn behind the menu; use it
when many objects would otherwise need the `exit` line.

## Room transitions

A persistent fader that goes dark, changes room, then fades back.

```gml
// obj_fade Create
alpha = 0;
fading_out = true;
target_room = room;
speed_per_step = 0.05;
persistent = true;

// Step
if (fading_out) {
    alpha += speed_per_step;
    if (alpha >= 1) { alpha = 1; fading_out = false; room_goto(target_room); }
} else {
    alpha -= speed_per_step;
    if (alpha <= 0) instance_destroy();
}

// Draw GUI
draw_set_alpha(alpha);
draw_set_colour(c_black);
draw_rectangle(0, 0, display_get_gui_width(), display_get_gui_height(), false);
draw_set_alpha(1);

// helper
function go_to_room(_room) {
    if (instance_exists(obj_fade)) exit;
    var f = instance_create_depth(0, 0, -10000, obj_fade);
    f.target_room = _room;
}
```

`room_goto` takes effect at the end of the current step, so code after it in the same event still runs.
