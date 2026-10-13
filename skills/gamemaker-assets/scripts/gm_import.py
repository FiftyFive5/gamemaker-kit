"""Bulk sprite import for gm.py.

  import-aseprite <project> <export.json> [--prefix spr_monkey] [--origin bottom-centre] [--folder F]
      Reads an Aseprite "Export Sprite Sheet" JSON (hash or array, with or without tags).
      Every tag becomes its own sprite (spr_monkey_walk, spr_monkey_idle, ...) with frame timing
      converted to frames per second. Without tags, all frames become one sprite.
  import-folder   <project> <folder> [--prefix spr_] [--origin ...] [--fps 10] [--folder F]
      Every sub-folder of PNGs, or every group of files named like walk_0.png walk_1.png,
      becomes one sprite.
"""
import json
import os
import re

import gm
from gm import Refused


def _clean(name):
    s = re.sub(r"[^A-Za-z0-9_]+", "_", name.strip()).strip("_").lower()
    if not s:
        s = "sprite"
    if s[0].isdigit():
        s = "_" + s
    return s


def _load_aseprite(path):
    gm.need_pillow()
    from PIL import Image
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    frames = data.get("frames")
    if isinstance(frames, dict):
        frames = list(frames.values())          # hash export keeps file order in Python 3.7+
    if not frames:
        raise Refused("%s has no frames - is it an Aseprite sprite sheet JSON?" % path)
    meta = data.get("meta") or {}
    image_path = os.path.join(os.path.dirname(os.path.abspath(path)), meta.get("image", ""))
    if not os.path.isfile(image_path):
        raise Refused("the sheet image %r named in the JSON was not found next to it" % meta.get("image"))
    sheet = Image.open(image_path).convert("RGBA")
    imgs, durations = [], []
    for fr in frames:
        r = fr["frame"]
        if fr.get("rotated"):
            raise Refused("rotated frames are not supported; export without 'rotate'")
        cell = sheet.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]))
        src = fr.get("sourceSize") or {"w": r["w"], "h": r["h"]}
        if fr.get("trimmed") or (src["w"], src["h"]) != (r["w"], r["h"]):
            full = Image.new("RGBA", (src["w"], src["h"]), (0, 0, 0, 0))
            off = fr.get("spriteSourceSize") or {"x": 0, "y": 0}
            full.paste(cell, (off["x"], off["y"]))
            cell = full
        imgs.append(cell)
        durations.append(fr.get("duration") or 100)
    tags = meta.get("frameTags") or []
    return imgs, durations, tags


def _fps(durations):
    avg = sum(durations) / float(len(durations))
    return 1000.0 / avg if avg > 0 else None


def cmd_import_aseprite(p, args):
    imgs, durations, tags = _load_aseprite(args.json)
    base = args.prefix or "spr_" + _clean(os.path.splitext(os.path.basename(args.json))[0])
    jobs = []
    if tags:
        for t in tags:
            a, b = int(t["from"]), int(t["to"])
            seq = list(range(a, b + 1))
            if t.get("direction") == "reverse":
                seq.reverse()
            elif t.get("direction") == "pingpong" and len(seq) > 2:
                seq = seq + seq[-2:0:-1]
            jobs.append(("%s_%s" % (base, _clean(t["name"])), [imgs[i] for i in seq], [durations[i] for i in seq]))
    else:
        jobs.append((base, imgs, durations))
    sizes = {j[1][0].size for j in jobs}
    if len(sizes) > 1:
        print("note: tags have different frame sizes %s" % sorted(sizes))
    for name, frames, durs in jobs:
        gm.create_sprite(p, name, frames, args.origin, args.folder, args.template, _fps(durs))
        print("sprite %-32s %2d frame(s) %dx%d  %.1f fps" % (name, len(frames), frames[0].size[0],
                                                             frames[0].size[1], _fps(durs) or 0))


def _group_folder(folder):
    groups = {}
    entries = sorted(os.listdir(folder))
    for e in entries:
        full = os.path.join(folder, e)
        if os.path.isdir(full):
            pngs = sorted((f for f in os.listdir(full) if f.lower().endswith(".png")), key=_natural)
            if pngs:
                groups[_clean(e)] = [os.path.join(full, f) for f in pngs]
    for e in entries:
        full = os.path.join(folder, e)
        if os.path.isfile(full) and e.lower().endswith(".png"):
            stem = os.path.splitext(e)[0]
            key = _clean(re.sub(r"[_\-\s]?\d+$", "", stem)) or _clean(stem)
            groups.setdefault(key, []).append(full)
    for k in groups:
        groups[k].sort(key=lambda f: _natural(os.path.basename(f)))
    return groups


def _natural(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def cmd_import_folder(p, args):
    gm.need_pillow()
    from PIL import Image
    if not os.path.isdir(args.folder_path):
        raise Refused("%s is not a folder" % args.folder_path)
    groups = _group_folder(args.folder_path)
    if not groups:
        raise Refused("no PNG files found in %s" % args.folder_path)
    prefix = args.prefix if args.prefix is not None else "spr_"
    for key, files in sorted(groups.items()):
        name = prefix + key if not key.startswith(prefix) else key
        imgs = [Image.open(f).convert("RGBA") for f in files]
        gm.create_sprite(p, name, imgs, args.origin, args.folder, args.template, args.fps)
        print("sprite %-32s %2d frame(s) %dx%d" % (name, len(imgs), imgs[0].size[0], imgs[0].size[1]))


def register_cli(common):
    sp = common("import-aseprite", help="Aseprite JSON export -> one sprite per tag")
    sp.add_argument("json")
    sp.add_argument("--prefix")
    sp.add_argument("--origin")
    sp.add_argument("--folder")
    sp.add_argument("--template")
    sp = common("import-folder", help="folder of PNGs -> sprites")
    sp.add_argument("folder_path")
    sp.add_argument("--prefix")
    sp.add_argument("--origin")
    sp.add_argument("--fps", type=float)
    sp.add_argument("--folder")
    sp.add_argument("--template")
    return {"import-aseprite": cmd_import_aseprite, "import-folder": cmd_import_folder}
