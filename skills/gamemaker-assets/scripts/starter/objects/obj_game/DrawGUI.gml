/// @description Pause screen and a small HUD
var gw = display_get_gui_width();
var gh = display_get_gui_height();

draw_set_colour(c_white);
draw_text(8, 8, "$" + string(global.money));

if (global.paused) {
    draw_set_alpha(0.6);
    draw_set_colour(c_black);
    draw_rectangle(0, 0, gw, gh, false);
    draw_set_alpha(1);
    draw_set_colour(c_white);
    draw_set_halign(fa_center);
    draw_set_valign(fa_middle);
    draw_text(gw / 2, gh / 2, "PAUSED\n\nEsc / Start to continue");
    draw_set_halign(fa_left);
    draw_set_valign(fa_top);
}
