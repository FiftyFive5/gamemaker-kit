/// gamemaker-kit: action-based input for local multiplayer.
/// Gameplay code asks input_pressed(player, "action") instead of checking keys directly.
/// Players 0 and 1 share the keyboard (left side / right side); gamepads take over a slot when connected.

#macro DEV_KEYS_LEFT  -1
#macro DEV_KEYS_RIGHT -2
#macro DEV_NONE       -99

function input_init(_players) {
    global.input_players = _players;
    global.input_device = array_create(_players, DEV_NONE);
    global.input_device[0] = DEV_KEYS_LEFT;
    if (_players > 1) global.input_device[1] = DEV_KEYS_RIGHT;

    global.input_keys = {};
    global.input_keys[$ string(DEV_KEYS_LEFT)]  = { up: ord("W"), down: ord("S"), left: ord("A"), right: ord("D"), action: ord("E"), drop: ord("Q") };
    global.input_keys[$ string(DEV_KEYS_RIGHT)] = { up: vk_up, down: vk_down, left: vk_left, right: vk_right, action: ord("L"), drop: ord("K") };
    global.input_pad = { up: gp_padu, down: gp_padd, left: gp_padl, right: gp_padr, action: gp_face1, drop: gp_face3, pause: gp_start };

    for (var i = 0; i < gamepad_get_device_count(); i++) {
        if (gamepad_is_connected(i)) input_pad_connected(i);
    }
}

/// Returns [x, y], each between -1 and 1.
function input_axis(_p) {
    if (_p >= array_length(global.input_device)) return [0, 0];
    var dev = global.input_device[_p];
    if (dev >= 0) {
        if (!gamepad_is_connected(dev)) return [0, 0];
        var ax = gamepad_axis_value(dev, gp_axislh);
        var ay = gamepad_axis_value(dev, gp_axislv);
        ax += gamepad_button_check(dev, gp_padr) - gamepad_button_check(dev, gp_padl);
        ay += gamepad_button_check(dev, gp_padd) - gamepad_button_check(dev, gp_padu);
        return [clamp(ax, -1, 1), clamp(ay, -1, 1)];
    }
    if (dev == DEV_NONE) return [0, 0];
    var k = global.input_keys[$ string(dev)];
    return [keyboard_check(k.right) - keyboard_check(k.left), keyboard_check(k.down) - keyboard_check(k.up)];
}

function input_pressed(_p, _action) {
    if (_p >= array_length(global.input_device)) return false;
    var dev = global.input_device[_p];
    if (dev >= 0) {
        var b = global.input_pad[$ _action];
        return !is_undefined(b) && gamepad_is_connected(dev) && gamepad_button_check_pressed(dev, b);
    }
    if (dev == DEV_NONE) return false;
    var key = global.input_keys[$ string(dev)][$ _action];
    return !is_undefined(key) && keyboard_check_pressed(key);
}

function input_held(_p, _action) {
    if (_p >= array_length(global.input_device)) return false;
    var dev = global.input_device[_p];
    if (dev >= 0) {
        var b = global.input_pad[$ _action];
        return !is_undefined(b) && gamepad_is_connected(dev) && gamepad_button_check(dev, b);
    }
    if (dev == DEV_NONE) return false;
    var key = global.input_keys[$ string(dev)][$ _action];
    return !is_undefined(key) && keyboard_check(key);
}

/// Any player pressed this action this step.
function input_any_pressed(_action) {
    for (var i = 0; i < array_length(global.input_device); i++) {
        if (input_pressed(i, _action)) return true;
    }
    return false;
}

function input_pad_connected(_pad) {
    var n = array_length(global.input_device);
    var i;
    for (i = 0; i < n; i++) {
        if (global.input_device[i] == _pad) return;   // already assigned
    }
    gamepad_set_axis_deadzone(_pad, 0.25);
    // first free slot, otherwise take over the first keyboard player
    for (i = 0; i < n; i++) {
        if (global.input_device[i] == DEV_NONE) { global.input_device[i] = _pad; return; }
    }
    for (i = 0; i < n; i++) {
        if (global.input_device[i] < 0) { global.input_device[i] = _pad; return; }
    }
}

/// Returns true if a player lost their controller (the game should pause).
/// Players 1 and 2 fall back to their keyboard side.
function input_pad_lost(_pad) {
    for (var i = 0; i < array_length(global.input_device); i++) {
        if (global.input_device[i] == _pad) {
            global.input_device[i] = (i == 0) ? DEV_KEYS_LEFT : ((i == 1) ? DEV_KEYS_RIGHT : DEV_NONE);
            return true;
        }
    }
    return false;
}
