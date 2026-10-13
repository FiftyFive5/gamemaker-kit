# Input layer, hot-plugging, cameras

## Input layer (script `scr_input`)

```gml
// Device kinds
#macro DEV_KEYS_LEFT  -1
#macro DEV_KEYS_RIGHT -2
#macro DEV_NONE       -99      // gamepad slots are 0 and up

function input_init(_players) {
    global.input_device = array_create(_players, DEV_NONE);
    global.input_device[0] = DEV_KEYS_LEFT;
    if (_players > 1) global.input_device[1] = DEV_KEYS_RIGHT;

    // keyboard bindings per keyboard side; values are key codes
    global.input_keys = {};
    global.input_keys[$ string(DEV_KEYS_LEFT)]  = { up: ord("W"), down: ord("S"), left: ord("A"), right: ord("D"), action: ord("E"), drop: ord("Q") };
    global.input_keys[$ string(DEV_KEYS_RIGHT)] = { up: vk_up, down: vk_down, left: vk_left, right: vk_right, action: ord("L"), drop: ord("K") };

    // gamepad bindings shared by all pads
    global.input_pad = { action: gp_face1, drop: gp_face3, pause: gp_start };
}

function input_axis(_p) {   // returns [x, y], each -1..1
    var dev = global.input_device[_p];
    if (dev >= 0) {
        if (!gamepad_is_connected(dev)) return [0, 0];
        return [gamepad_axis_value(dev, gp_axislh), gamepad_axis_value(dev, gp_axislv)];
    }
    if (dev == DEV_NONE) return [0, 0];
    var k = global.input_keys[$ string(dev)];
    return [keyboard_check(k.right) - keyboard_check(k.left), keyboard_check(k.down) - keyboard_check(k.up)];
}

function input_pressed(_p, _action) {
    var dev = global.input_device[_p];
    if (dev >= 0) return gamepad_is_connected(dev) && gamepad_button_check_pressed(dev, global.input_pad[$ _action]);
    if (dev == DEV_NONE) return false;
    return keyboard_check_pressed(global.input_keys[$ string(dev)][$ _action]);
}

function input_held(_p, _action) {
    var dev = global.input_device[_p];
    if (dev >= 0) return gamepad_is_connected(dev) && gamepad_button_check(dev, global.input_pad[$ _action]);
    if (dev == DEV_NONE) return false;
    return keyboard_check(global.input_keys[$ string(dev)][$ _action]);
}
```

Usage in a player object:

```gml
// spawned with: instance_create_layer(x, y, "Instances", obj_player, { player_index: 1 });
// Step
var ax = input_axis(player_index);
if (point_distance(0, 0, ax[0], ax[1]) > 0.2) {
    var dir = point_direction(0, 0, ax[0], ax[1]);
    hsp = lengthdir_x(walk_speed, dir);
    vsp = lengthdir_y(walk_speed, dir);
}
if (input_pressed(player_index, "action")) { /* grab / throw */ }
```

Call `input_init(2)` once in the controller's Create before any player exists. Add actions by adding keys to
both keyboard structs and the pad struct.

Mouse aiming for a keyboard player: `point_direction(x, y, mouse_x, mouse_y)`; for a gamepad player use the right
stick (`gp_axisrh`, `gp_axisrv`) and keep the last direction when the stick is centred.

## Rebinding

Wait for the next key press and store it:

```gml
// menu object Step, while waiting for a key for (side, action)
if (keyboard_check_pressed(vk_anykey) && keyboard_lastkey != vk_escape) {
    global.input_keys[$ string(rebind_side)][$ rebind_action] = keyboard_lastkey;
    rebinding = false;
}
```

Reject a key already used by the other side, and save `global.input_keys` with the settings (structs serialise
with `json_stringify`).

## Gamepad hot-plugging (controller object, Async – System event)

```gml
var type = async_load[? "event_type"];
if (type == "gamepad discovered") {
    var pad = async_load[? "pad_index"];
    gamepad_set_axis_deadzone(pad, 0.25);
    // give it to the first player without a device, else the first keyboard player
    var slot = array_get_index(global.input_device, DEV_NONE);
    if (slot < 0) slot = array_get_index(global.input_device, DEV_KEYS_LEFT);
    if (slot >= 0) global.input_device[slot] = pad;
} else if (type == "gamepad lost") {
    var pad = async_load[? "pad_index"];
    var slot = array_get_index(global.input_device, pad);
    if (slot >= 0) {
        global.input_device[slot] = DEV_NONE;
        global.paused = true;   // let the player reconnect instead of silently dropping them
    }
}
```

`array_get_index` exists in recent versions; on older ones write a small loop. Pads connected before the game
starts also send "gamepad discovered" at startup on most platforms; to be safe, also scan
`for (var i = 0; i < gamepad_get_device_count(); i++) if (gamepad_is_connected(i)) …` once in Create.

## Shared camera (frames every player)

```gml
// camera End Step: centre on all players, zoom out when they spread
var minx = infinity, miny = infinity, maxx = -infinity, maxy = -infinity, n = 0;
with (obj_player) {
    minx = min(minx, x); maxx = max(maxx, x);
    miny = min(miny, y); maxy = max(maxy, y);
    n++;
}
if (n > 0) {
    var margin = 64;
    var need_w = max(base_w, (maxx - minx) + margin * 2);
    var need_h = max(base_h, (maxy - miny) + margin * 2);
    var zoom = clamp(max(need_w / base_w, need_h / base_h), 1, max_zoom);   // max_zoom e.g. 1.5
    view_w = lerp(view_w, base_w * zoom, 0.1);
    view_h = lerp(view_h, base_h * zoom, 0.1);
    x = lerp(x, (minx + maxx) / 2, 0.15);
    y = lerp(y, (miny + maxy) / 2, 0.15);
}
camera_set_view_size(cam, view_w, view_h);
// then clamp and set the position as in gml-systems → Camera
```

Note how the `with (obj_player)` block writes the camera's locals (`minx`, `n`, …): locals declared before a
`with` are shared with it. When players hit `max_zoom`, keep the camera at the limit and push players back
inside the view (clamp their x/y to the view rectangle) rather than letting one leave the screen.

## Split screen (two views)

```gml
// Room Start, two players side by side on a 640x360 window
view_enabled = true;
for (var i = 0; i < 2; i++) {
    view_visible[i] = true;
    view_xport[i] = i * 320; view_yport[i] = 0;
    view_wport[i] = 320;     view_hport[i] = 360;
    view_camera[i] = camera_create_view(0, 0, 320, 360);
}
// End Step: camera i follows player i (find the instance with player_index == i)
```

Destroy cameras created with `camera_create_view` (`camera_destroy`) when leaving the room. Draw GUI runs once for
the whole window; per-view HUD belongs in the Draw event using `view_current` to know which view is drawing.
