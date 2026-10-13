/// @description Top-down movement with wall collision, plus a juice demo on the action button
if (global.paused || global.hitstop > 0) exit;

var ax = input_axis(player_index);
var amount = min(1, point_distance(0, 0, ax[0], ax[1]));
if (amount > 0.2) {
    var dir = point_direction(0, 0, ax[0], ax[1]);
    hsp = lengthdir_x(walk_speed * amount, dir);
    vsp = lengthdir_y(walk_speed * amount, dir);
    if (ax[0] != 0) facing = sign(ax[0]);
} else {
    hsp = 0;
    vsp = 0;
}

// move one axis at a time so walls stop you cleanly
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

// juice demo: press the action button (E / L / A on a gamepad)
if (input_pressed(player_index, "action")) {
    draw_xscale = 1.35;
    draw_yscale = 0.7;
    flash = 3;
    juice_burst(x, y, 12);
    juice_shake(0.25);
    juice_text(x, y - 14, choose("BONK!", "HEY!", "+1"));
    global.money += 1;
}

draw_xscale = lerp(draw_xscale, 1, 0.2);
draw_yscale = lerp(draw_yscale, 1, 0.2);
flash = max(0, flash - 1);
depth = -y;
