/// @description Pause toggle, quick restart
if (keyboard_check_pressed(vk_escape) || input_any_pressed("pause")) {
    global.paused = !global.paused;
    if (global.paused) audio_pause_all(); else audio_resume_all();
}
if (global.paused) exit;

// F5-style quick restart of the current room while prototyping
if (keyboard_check_pressed(ord("R")) && keyboard_check(vk_control)) room_restart();
