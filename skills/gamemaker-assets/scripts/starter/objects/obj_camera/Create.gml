/// @description Persistent camera that frames every player, zooms out when they spread, and shakes
view_w = 320;
view_h = 180;
window_scale = 3;
smooth = 0.12;
max_zoom = 1.6;
zoom = 1;
window_sized = false;
cam = camera_create_view(0, 0, view_w, view_h);

camera_setup = function() {
    view_enabled = true;
    view_visible[0] = true;
    view_camera[0] = cam;
    view_xport[0] = 0;
    view_yport[0] = 0;
    view_wport[0] = view_w * window_scale;
    view_hport[0] = view_h * window_scale;
    if (!window_sized) {
        window_set_size(view_w * window_scale, view_h * window_scale);
        surface_resize(application_surface, view_w * window_scale, view_h * window_scale);
        window_center();
        window_sized = true;
    }
    // jump straight to the players instead of sliding in from the corner
    var n = 0, sx = 0, sy = 0;
    with (obj_player) { sx += x; sy += y; n++; }
    if (n > 0) { x = sx / n; y = sy / n; }
};
camera_setup();
