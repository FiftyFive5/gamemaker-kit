/// @description Draw with squash/stretch, hit flash and a player tag
if (flash > 0) gpu_set_fog(true, c_white, 0, 0);
draw_sprite_ext(sprite_index, image_index, x, y, draw_xscale * facing, draw_yscale, 0, image_blend, image_alpha);
if (flash > 0) gpu_set_fog(false, c_white, 0, 0);

draw_set_halign(fa_center);
draw_set_valign(fa_bottom);
draw_text_transformed(x, bbox_top - 2, "P" + string(player_index + 1), 0.5, 0.5, 0);
draw_set_halign(fa_left);
draw_set_valign(fa_top);
