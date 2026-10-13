/// @description Build the text level for this room and make sure a camera exists
level_build_for_room();
if (!instance_exists(obj_camera)) instance_create_depth(0, 0, 0, obj_camera);
with (obj_camera) camera_setup();
