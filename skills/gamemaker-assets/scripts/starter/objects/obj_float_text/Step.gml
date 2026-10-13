/// @description Rise and fade
if (global.paused || global.hitstop > 0) exit;
y += vy;
vy *= 0.93;
life--;
if (life <= 0) instance_destroy();
