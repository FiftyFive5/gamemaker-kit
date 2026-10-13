/// gamemaker-kit: save and load any struct as JSON in the game's save folder.
/// save_struct("save.json", { money: 10 });  var data = load_struct("save.json", { money: 0 });
/// load_struct fills keys missing from the file with the defaults, so old saves keep loading.

function save_struct(_file, _struct) {
    var json = json_stringify(_struct);
    var buf = buffer_create(string_byte_length(json) + 1, buffer_fixed, 1);
    buffer_write(buf, buffer_string, json);
    buffer_save(buf, _file);
    buffer_delete(buf);
}

function load_struct(_file, _defaults) {
    var result = {};
    var dkeys = variable_struct_get_names(_defaults);
    for (var d = 0; d < array_length(dkeys); d++) {
        result[$ dkeys[d]] = _defaults[$ dkeys[d]];
    }
    if (!file_exists(_file)) return result;
    var buf = buffer_load(_file);
    if (buf == -1) return result;
    var json = buffer_read(buf, buffer_string);
    buffer_delete(buf);
    var data;
    try {
        data = json_parse(json);
    } catch (_e) {
        show_debug_message("gamemaker-kit: could not read " + _file + ", using defaults");
        return result;
    }
    if (!is_struct(data)) return result;
    var keys = variable_struct_get_names(data);
    for (var i = 0; i < array_length(keys); i++) {
        result[$ keys[i]] = data[$ keys[i]];
    }
    return result;
}

function settings_save() {
    save_struct("settings.json", global.settings);
}

function settings_load() {
    global.settings = load_struct("settings.json", { music: 1, sfx: 1, shake: 1, fullscreen: false });
    global.shake_scale = global.settings.shake;
    window_set_fullscreen(global.settings.fullscreen);
}
