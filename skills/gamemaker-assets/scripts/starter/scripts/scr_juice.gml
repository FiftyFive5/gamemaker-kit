/// gamemaker-kit: game-feel helpers. Call juice_init() once (obj_game does it).
/// juice_shake(0.2..0.6), juice_hitstop(frames), juice_burst(x, y, count), juice_text(x, y, text), sfx(snd)

function juice_init() {
    if (!variable_global_exists("paused")) global.paused = false;
    global.trauma = 0;
    global.hitstop = 0;
    global.shake_scale = 1;          // settings: 0 turns screen shake off

    global.juice_ps = part_system_create();
    part_system_depth(global.juice_ps, -1000);

    global.pt_spark = part_type_create();
    part_type_shape(global.pt_spark, pt_shape_pixel);
    part_type_size(global.pt_spark, 1, 2, -0.02, 0);
    part_type_colour2(global.pt_spark, c_white, c_yellow);
    part_type_alpha2(global.pt_spark, 1, 0);
    part_type_speed(global.pt_spark, 0.8, 2.2, -0.06, 0);
    part_type_direction(global.pt_spark, 0, 360, 0, 0);
    part_type_life(global.pt_spark, 12, 26);

    global.pt_dust = part_type_create();
    part_type_shape(global.pt_dust, pt_shape_pixel);
    part_type_size(global.pt_dust, 1, 3, -0.03, 0);
    part_type_colour2(global.pt_dust, c_ltgray, c_gray);
    part_type_alpha2(global.pt_dust, 0.8, 0);
    part_type_speed(global.pt_dust, 0.2, 0.7, -0.02, 0);
    part_type_direction(global.pt_dust, 60, 120, 0, 0);
    part_type_life(global.pt_dust, 15, 30);
}

function juice_cleanup() {
    part_type_destroy(global.pt_spark);
    part_type_destroy(global.pt_dust);
    part_system_destroy(global.juice_ps);
}

/// Screen shake using the trauma model: small hits stay subtle, big hits are strong.
function juice_shake(_amount) {
    global.trauma = min(1, global.trauma + _amount);
}

/// Freeze gameplay for a few frames (3-6 normal, 8-12 big).
function juice_hitstop(_frames) {
    global.hitstop = max(global.hitstop, _frames);
}

function juice_burst(_x, _y, _count, _type = global.pt_spark) {
    part_particles_create(global.juice_ps, _x, _y, _type, _count);
}

function juice_text(_x, _y, _text, _colour = c_white) {
    return instance_create_depth(_x, _y, -2000, obj_float_text, { text: string(_text), colour: _colour });
}

/// Play a sound with slight random pitch so repeats do not sound mechanical.
function sfx(_snd, _pitch_var = 0.1) {
    var inst = audio_play_sound(_snd, 10, false);
    audio_sound_pitch(inst, 1 + random_range(-_pitch_var, _pitch_var));
    return inst;
}

/// Everything at once for a strong impact.
function juice_big_hit(_x, _y) {
    juice_hitstop(6);
    juice_shake(0.4);
    juice_burst(_x, _y, 14);
}
