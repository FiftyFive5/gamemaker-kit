"""Starter kit and drop-in systems for gm.py.

  starter     <project> [--genre topdown|platformer] [--prefix kit_] [--folder F]
  add-system  <project> input juice save level camera fade [--prefix ...] [--folder F]

Everything is cloned from the project's own templates (see gm.py); GML comes from ./starter/.
"""
import os
import re

import gm
from gm import Refused

HERE = os.path.dirname(os.path.abspath(__file__))
STARTER = os.path.join(HERE, "starter")

# what each system adds; objects: (name, [event specs], sprite, persistent)
SYSTEMS = {
    "input":  {"scripts": ["scr_input"], "objects": [], "needs": []},
    "juice":  {"scripts": ["scr_juice"], "objects": [("obj_float_text", ["Create", "Step", "Draw"], None, False)],
               "needs": []},
    "save":   {"scripts": ["scr_save"], "objects": [], "needs": []},
    "level":  {"scripts": ["scr_level"], "objects": [], "needs": []},
    "fade":   {"scripts": ["scr_transition"], "objects": [("obj_fade", ["Create", "Step", "DrawGUI"], None, True)],
               "needs": []},
    "camera": {"scripts": [], "objects": [("obj_camera", ["Create", "EndStep", "CleanUp"], None, True)],
               "needs": ["juice", "level"]},
}
STARTER_OBJECTS = [
    ("obj_wall", [], "spr_wall", False),
    ("obj_player", ["Create", "Step", "Draw"], "spr_player", False),
    ("obj_game", ["Create", "BeginStep", "Step", "RoomStart", "DrawGUI", "AsyncSystem", "CleanUp"], None, True),
]
EVENT_FILE = {"Create": "Create", "Step": "Step", "Draw": "Draw", "DrawGUI": "DrawGUI", "EndStep": "EndStep",
              "BeginStep": "BeginStep", "RoomStart": "RoomStart", "AsyncSystem": "AsyncSystem",
              "CleanUp": "CleanUp"}
KIT_FUNCTIONS = ["input_init", "input_axis", "input_pressed", "input_held", "input_any_pressed",
                 "input_pad_connected", "input_pad_lost", "juice_init", "juice_cleanup", "juice_shake",
                 "juice_hitstop", "juice_burst", "juice_text", "sfx", "juice_big_hit", "save_struct",
                 "load_struct", "settings_save", "settings_load", "level_legend_set", "level_build",
                 "level_build_for_room", "fade_to_room"]

LEVELS = {
    "topdown": [
        "##############################",
        "#............................#",
        "#..P......................Q..#",
        "#............................#",
        "#.....####..........####.....#",
        "#.....#................#.....#",
        "#.....#................#.....#",
        "#............................#",
        "#..........######............#",
        "#............................#",
        "#.....#................#.....#",
        "#.....#................#.....#",
        "#.....####..........####.....#",
        "#............................#",
        "#............................#",
        "#............................#",
        "##############################",
    ],
    "platformer": [
        "##############################",
        "#............................#",
        "#............................#",
        "#.......................###..#",
        "#............................#",
        "#..............####..........#",
        "#............................#",
        "#.....####...................#",
        "#.......................####.#",
        "#............................#",
        "#..P.......####...........Q..#",
        "##############################",
    ],
}


def _read(rel):
    with open(os.path.join(STARTER, rel), "r", encoding="utf-8") as f:
        return f.read()


def _rename_code(code, mapping):
    for old, new in mapping.items():
        code = re.sub(r"\b%s\b" % re.escape(old), new, code)
    return code


def _existing_functions(p):
    found = set()
    for root, _, files in os.walk(p.root):
        for fn in files:
            if fn.endswith(".gml"):
                try:
                    with open(os.path.join(root, fn), "r", encoding="utf-8", errors="replace") as f:
                        found.update(re.findall(r"\bfunction\s+([A-Za-z_]\w*)", f.read()))
                except OSError:
                    pass
    return found


def _sprite_images(kind):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if kind == "spr_player":
        d.rounded_rectangle((2, 2, 13, 15), radius=4, fill=(35, 30, 45, 255))          # outline
        d.rounded_rectangle((3, 3, 12, 14), radius=3, fill=(240, 240, 235, 255))       # body (tinted per player)
        d.rectangle((5, 6, 6, 8), fill=(30, 30, 40, 255))                               # eyes
        d.rectangle((9, 6, 10, 8), fill=(30, 30, 40, 255))
        d.rectangle((6, 11, 9, 11), fill=(200, 120, 120, 255))                          # mouth
    else:  # spr_wall: bricks
        d.rectangle((0, 0, 15, 15), fill=(70, 74, 92, 255))
        for y in (0, 8):
            d.line((0, y, 15, y), fill=(50, 52, 66, 255))
        for x, y0 in ((7, 1), (3, 9), (11, 9)):
            d.line((x, y0, x, y0 + 6), fill=(50, 52, 66, 255))
        d.line((0, 1, 15, 1), fill=(96, 100, 122, 255))
        d.line((0, 9, 15, 9), fill=(96, 100, 122, 255))
    return [img]


def _install(p, systems, with_game, genre, prefix, folder):
    # resolve dependencies
    todo = []

    def add(s):
        if s not in SYSTEMS:
            raise Refused("unknown system %r (choose from %s)" % (s, ", ".join(SYSTEMS)))
        for dep in SYSTEMS[s]["needs"]:
            add(dep)
        if s not in todo:
            todo.append(s)
    for s in systems:
        add(s)

    scripts = [n for s in todo for n in SYSTEMS[s]["scripts"]]
    objects = [o for s in todo for o in SYSTEMS[s]["objects"]]
    sprites = []
    if with_game:
        objects = STARTER_OBJECTS[:2] + objects + STARTER_OBJECTS[2:]
        sprites = ["spr_player", "spr_wall"]

    all_names = scripts + [o[0] for o in objects] + sprites
    mapping = {n: prefix + n for n in all_names} if prefix else {}
    final = [mapping.get(n, n) for n in all_names]
    clashes = [n for n in final if n in p.names]
    if clashes:
        raise Refused("these names already exist in the project: %s. Run again with --prefix (for example "
                      "--prefix kit_) or add only the systems you are missing." % ", ".join(clashes))
    fclash = sorted(set(KIT_FUNCTIONS) & _existing_functions(p))
    if fclash:
        raise Refused("the project already defines functions with the kit's names: %s. Install only the "
                      "systems you do not have yet." % ", ".join(fclash))

    if sprites:
        gm.need_pillow()
        for s in sprites:
            gm.create_sprite(p, mapping.get(s, s), _sprite_images(s), "middle-centre", folder)

    for s in scripts:
        code = _read("scripts/%s.gml" % s)
        if s == "scr_level":
            code = code.replace("{{LEGEND_AND_LEVELS}}", _legend_code(with_game, genre))
        gm.create_script(p, mapping.get(s, s), _rename_code(code, mapping), folder)

    # objects without events first so collision/sprite references resolve
    for name, events, sprite, persistent in objects:
        code = {}
        for spec in events:
            fname = EVENT_FILE[spec]
            rel = "objects/%s/%s.gml" % (name, fname)
            if name == "obj_player" and spec == "Step":
                rel = "objects/obj_player/Step.%s.gml" % genre
            code[spec] = _rename_code(_read(rel), mapping)
        gm.create_object(p, mapping.get(name, name), events, code=code,
                         sprite=mapping.get(sprite, sprite) if sprite else None,
                         folder=folder, persistent=persistent)
    return [mapping.get(n, n) for n in all_names]


def _legend_code(with_game, genre):
    if not with_game:
        return ('// Example:\n'
                '// level_legend_set("#", obj_wall);\n'
                '// level_legend_set("P", obj_player, { player_index: 0 });\n'
                '// global.levels[$ "rm_level1"] = [\n//     "#####",\n//     "#P..#",\n//     "#####",\n// ];\n')
    rows = ",\n".join('    "%s"' % r for r in LEVELS[genre])
    return ('level_legend_set("#", obj_wall);\n'
            'level_legend_set("P", obj_player, { player_index: 0 });\n'
            'level_legend_set("Q", obj_player, { player_index: 1 });\n\n'
            '// "default" is used for every room that has no level of its own. Give a room its own level with\n'
            '// global.levels[$ "rm_name"] = [ ... ];  Remove "default" once your real rooms have levels.\n'
            'global.levels[$ "default"] = [\n%s,\n];\n' % rows)


def cmd_starter(p, args):
    names = _install(p, list(SYSTEMS), True, args.genre, args.prefix or "", args.folder)
    game = (args.prefix or "") + "obj_game"
    print("starter kit (%s): %s" % (args.genre, ", ".join(names)))
    print("ONE manual step: in the IDE, drag %s into your first room (any layer). Then run the game:" % game)
    print("  P1 = WASD + E, P2 = arrows + L (gamepads take over automatically), Esc = pause, Ctrl+R = restart")


def cmd_add_system(p, args):
    names = _install(p, args.systems, False, "topdown", args.prefix or "", args.folder)
    print("added: %s" % ", ".join(names))
    if "input" in args.systems:
        print("note: call input_init(<players>) once, e.g. in your controller's Create")
    if any(s in args.systems for s in ("juice", "camera")):
        print("note: call juice_init() once in your controller's Create (camera shake reads its values)")
    if any(s in args.systems for s in ("level", "camera")):
        print("note: call level_build_for_room() in your controller's Room Start; for the camera, create it "
              "there too and run: with (obj_camera) camera_setup();")


def register_cli(common):
    sp = common("starter", help="install a playable starter game")
    sp.add_argument("--genre", choices=sorted(LEVELS), default="topdown")
    sp.add_argument("--prefix")
    sp.add_argument("--folder")
    sp = common("add-system", help="add individual systems")
    sp.add_argument("systems", nargs="+", choices=sorted(SYSTEMS))
    sp.add_argument("--prefix")
    sp.add_argument("--folder")
    return {"starter": cmd_starter, "add-system": cmd_add_system}
