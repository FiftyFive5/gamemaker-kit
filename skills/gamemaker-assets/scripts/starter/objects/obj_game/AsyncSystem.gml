/// @description Gamepads connecting and disconnecting
var type = async_load[? "event_type"];
if (type == "gamepad discovered") {
    input_pad_connected(async_load[? "pad_index"]);
    if (paused_by_pad) { global.paused = false; paused_by_pad = false; audio_resume_all(); }
} else if (type == "gamepad lost") {
    if (input_pad_lost(async_load[? "pad_index"]) && !global.paused) {
        global.paused = true;
        paused_by_pad = true;
        audio_pause_all();
    }
}
