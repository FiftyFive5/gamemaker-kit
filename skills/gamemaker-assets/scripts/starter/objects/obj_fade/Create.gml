/// @description Fade to black, change room, fade back (create with fade_to_room)
if (!variable_instance_exists(id, "target_room")) target_room = room;
alpha = 0;
fading_out = true;
fade_speed = 0.06;
