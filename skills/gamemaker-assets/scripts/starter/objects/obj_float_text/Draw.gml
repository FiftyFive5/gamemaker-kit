/// @description Draw
draw_set_halign(fa_center);
draw_set_valign(fa_middle);
draw_set_alpha(min(1, life / 15));
draw_set_colour(c_black);
draw_text_transformed(x + 1, y + 1, text, 0.6, 0.6, 0);
draw_set_colour(colour);
draw_text_transformed(x, y, text, 0.6, 0.6, 0);
draw_set_alpha(1);
draw_set_colour(c_white);
draw_set_halign(fa_left);
draw_set_valign(fa_top);
