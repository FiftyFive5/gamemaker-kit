/// gamemaker-kit: fade_to_room(rm_next) fades to black, changes room and fades back in.
function fade_to_room(_room) {
    if (instance_exists(obj_fade)) return;
    instance_create_depth(0, 0, -10000, obj_fade, { target_room: _room });
}
