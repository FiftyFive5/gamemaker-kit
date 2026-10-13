/// @description Platformer movement: coyote time, jump buffer, variable jump height, landing squash
if (global.paused || global.hitstop > 0) exit;

var ax = input_axis(player_index);
hsp = ax[0] * run_speed;
if (ax[0] != 0) facing = sign(ax[0]);

var on_ground = place_meeting(x, y + 1, obj_wall);
coyote = on_ground ? 0 : coyote + 1;
var jump_pressed = input_pressed(player_index, "action") || input_pressed(player_index, "up");
var jump_held = input_held(player_index, "action") || input_held(player_index, "up");
jump_buffer = jump_pressed ? 0 : jump_buffer + 1;

if (jump_buffer <= 6 && coyote <= 6) {
    vsp = -jump_speed;
    jump_buffer = 99;
    coyote = 99;
    draw_xscale = 0.75;
    draw_yscale = 1.3;
    juice_burst(x, bbox_bottom, 6, global.pt_dust);
}
if (vsp < 0 && !jump_held) vsp = max(vsp, -jump_speed * 0.45);   // release early = shorter jump
vsp = min(vsp + grav, max_fall);

var fall_speed = vsp;
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

var landed = place_meeting(x, y + 1, obj_wall);
if (landed && !was_on_ground && fall_speed > 1.5) {
    draw_xscale = 1.3;
    draw_yscale = 0.75;
    juice_burst(x, bbox_bottom, 8, global.pt_dust);
    if (fall_speed >= max_fall) juice_shake(0.2);
}
was_on_ground = landed;

draw_xscale = lerp(draw_xscale, 1, 0.2);
draw_yscale = lerp(draw_yscale, 1, 0.2);
flash = max(0, flash - 1);
