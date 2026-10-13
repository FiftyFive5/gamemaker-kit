/// @description Fade logic
if (fading_out) {
    alpha += fade_speed;
    if (alpha >= 1) {
        alpha = 1;
        fading_out = false;
        room_goto(target_room);
    }
} else {
    alpha -= fade_speed;
    if (alpha <= 0) instance_destroy();
}
