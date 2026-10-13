/// @description Follow the middle of all players, zoom to fit, clamp to the level, apply shake
var minx = infinity, miny = infinity, maxx = -infinity, maxy = -infinity, n = 0;
with (obj_player) {
    minx = min(minx, x); maxx = max(maxx, x);
    miny = min(miny, y); maxy = max(maxy, y);
    n++;
}
if (n > 0) {
    var margin = 48;
    var need = max(((maxx - minx) + margin * 2) / view_w, ((maxy - miny) + margin * 2) / view_h);
    zoom = lerp(zoom, clamp(need, 1, max_zoom), 0.08);
    x = lerp(x, (minx + maxx) / 2, smooth);
    y = lerp(y, (miny + maxy) / 2, smooth);
}

var vw = view_w * zoom;
var vh = view_h * zoom;
camera_set_view_size(cam, vw, vh);

var lw = variable_global_exists("level_w") && global.level_w > 0 ? global.level_w : room_width;
var lh = variable_global_exists("level_h") && global.level_h > 0 ? global.level_h : room_height;
var cx = (lw > vw) ? clamp(x - vw / 2, 0, lw - vw) : (lw - vw) / 2;
var cy = (lh > vh) ? clamp(y - vh / 2, 0, lh - vh) : (lh - vh) / 2;

if (variable_global_exists("trauma")) {
    var s = global.trauma * global.trauma * 8 * global.shake_scale;
    cx += random_range(-s, s);
    cy += random_range(-s, s);
    global.trauma = max(0, global.trauma - 0.03);
}
camera_set_view_pos(cam, floor(cx), floor(cy));
