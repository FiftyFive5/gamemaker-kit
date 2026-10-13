/// @description Player setup (player_index comes from the level legend or the creation struct)
if (!variable_instance_exists(id, "player_index")) player_index = 0;

hsp = 0;
vsp = 0;
facing = 1;

// top-down
walk_speed = 1.8;

// platformer
run_speed = 2;
jump_speed = 4.6;
grav = 0.25;
max_fall = 6;
coyote = 99;
jump_buffer = 99;
was_on_ground = false;

// feel
draw_xscale = 1;
draw_yscale = 1;
flash = 0;
image_speed = 0;
image_blend = (player_index == 0) ? c_white : make_colour_rgb(255, 180, 130);
