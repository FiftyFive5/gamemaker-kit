/// @description gamemaker-kit: game controller (one per game, persistent)
// Only one controller may exist; a second copy (e.g. when its room is revisited) removes itself.
owns_juice = false;
if (instance_number(obj_game) > 1) { instance_destroy(); exit; }

global.paused = false;
global.money = 0;

input_init(2);          // two local players: WASD+E / arrows+L, gamepads take over when connected
juice_init();
owns_juice = true;
settings_load();
randomize();

paused_by_pad = false;
