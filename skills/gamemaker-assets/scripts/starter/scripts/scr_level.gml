/// gamemaker-kit: build levels from text, no Room Editor needed.
/// Each character is one cell. Add your own characters with level_legend_set("M", obj_monkey).
/// Levels are looked up by room name: global.levels[$ "rm_zoo"] = [ "#####", "#P.M#", "#####" ];
/// obj_game builds the level for the current room at Room Start (see level_build_for_room).

global.level_cell = 16;           // pixel size of one character
global.level_w = 0;               // filled in by level_build: level size in pixels
global.level_h = 0;
global.level_legend = {};
global.levels = {};

function level_legend_set(_char, _object, _vars = {}) {
    global.level_legend[$ _char] = { obj: _object, vars: _vars };
}

/// Creates the instances for a level. Returns the number of instances created.
function level_build(_rows) {
    var cell = global.level_cell;
    var created = 0;
    var widest = 0;
    for (var r = 0; r < array_length(_rows); r++) {
        var line = _rows[r];
        widest = max(widest, string_length(line));
        for (var c = 1; c <= string_length(line); c++) {
            var entry = global.level_legend[$ string_char_at(line, c)];
            if (is_undefined(entry)) continue;
            instance_create_depth((c - 1) * cell + cell / 2, r * cell + cell / 2, 0, entry.obj, entry.vars);
            created++;
        }
    }
    global.level_w = widest * cell;
    global.level_h = array_length(_rows) * cell;
    return created;
}

/// Builds the level registered for the current room (or the "default" level), if any.
function level_build_for_room() {
    var rows = global.levels[$ room_get_name(room)];
    if (is_undefined(rows)) rows = global.levels[$ "default"];
    if (is_undefined(rows)) {
        global.level_w = room_width;
        global.level_h = room_height;
        return 0;
    }
    return level_build(rows);
}

// ---------------------------------------------------------------- legend and levels
{{LEGEND_AND_LEVELS}}
