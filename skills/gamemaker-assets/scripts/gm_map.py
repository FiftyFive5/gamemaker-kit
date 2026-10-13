"""Project scan, HTML project map and unused-asset finder for gm.py.

  map     <project> [-o project-map.html]
  unused  <project> [--remove name1,name2 | --remove all]
"""
import base64
import html
import io
import json
import os
import re
from collections import defaultdict

import gm
from gm import Refused, YYFile

KIND_BY_DIR = {"objects": "object", "sprites": "sprite", "scripts": "script", "rooms": "room",
               "sounds": "sound", "fonts": "font", "paths": "path", "sequences": "sequence",
               "tilesets": "tileset", "timelines": "timeline", "shaders": "shader", "animcurves": "animcurve",
               "notes": "note", "extensions": "extension", "particles": "particle"}
NEVER_UNUSED = {"room", "note", "extension", "tileset"}
EVENT_NAMES = {(0, 0): "Create", (1, 0): "Destroy", (12, 0): "Clean Up", (14, 0): "Pre-Create",
               (3, 0): "Step", (3, 1): "Begin Step", (3, 2): "End Step", (8, 0): "Draw", (8, 64): "Draw GUI",
               (8, 72): "Draw Begin", (8, 73): "Draw End", (8, 74): "Draw GUI Begin", (8, 75): "Draw GUI End",
               (8, 76): "Pre-Draw", (8, 77): "Post-Draw", (8, 65): "Resize", (7, 2): "Game Start",
               (7, 3): "Game End", (7, 4): "Room Start", (7, 5): "Room End", (7, 7): "Animation End",
               (7, 75): "Async System", (7, 62): "Async HTTP", (7, 69): "Async Steam"}
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
STRING_RE = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def event_name(et, en, other=None):
    if et == 4:
        return "Collision · %s" % other
    if et == 2:
        return "Alarm %d" % en
    if et == 7 and 10 <= en <= 25:
        return "User Event %d" % (en - 10)
    if et in (5, 9, 10):
        return "%s %s" % ({5: "Key", 9: "Key Press", 10: "Key Release"}[et], chr(en) if 48 <= en <= 90 else en)
    return EVENT_NAMES.get((et, en), "Event %d/%d" % (et, en))


def _strings_in(data, out):
    if isinstance(data, dict):
        for v in data.values():
            _strings_in(v, out)
    elif isinstance(data, list):
        for v in data:
            _strings_in(v, out)
    elif isinstance(data, str):
        out.add(data)


class Scan:
    """Everything the map, unused finder and rename need to know about a project."""

    def __init__(self, p):
        self.p = p
        self.assets = {}          # name -> dict(kind, path, data)
        self.gml = {}             # owner asset name -> {relpath: text}
        self.functions = defaultdict(list)   # script name -> [function names]
        self.refs = defaultdict(set)         # target name -> {referencing asset names}
        self.room_instances = defaultdict(lambda: defaultdict(int))  # room -> object -> count
        for name, path in p.resources:
            kind = KIND_BY_DIR.get(path.split("/")[0], "other")
            try:
                data = YYFile(p.abs(path)).data
            except (ValueError, OSError):
                data = {}
            self.assets[name] = {"kind": kind, "path": path, "data": data}
        names = set(self.assets)

        # code
        for name, a in self.assets.items():
            folder = os.path.dirname(p.abs(a["path"]))
            files = {}
            if os.path.isdir(folder):
                for fn in sorted(os.listdir(folder)):
                    if fn.endswith(".gml"):
                        try:
                            with open(os.path.join(folder, fn), "r", encoding="utf-8-sig", errors="replace") as f:
                                files[fn] = f.read()
                        except OSError:
                            pass
            self.gml[name] = files
            if a["kind"] == "script":
                for text in files.values():
                    self.functions[name] += re.findall(r"\bfunction\s+([A-Za-z_]\w*)", text)
        func_owner = {fn: s for s, fns in self.functions.items() for fn in fns}

        for name, files in self.gml.items():
            tokens = set()
            for text in files.values():
                code = COMMENT_RE.sub(" ", text)
                tokens.update(TOKEN_RE.findall(code))
                for lit in STRING_RE.findall(code):        # asset_get_index("spr_x") etc.
                    tokens.add(lit[1:-1])
            for t in tokens:
                if t in names and t != name:
                    self.refs[t].add(name)
                owner = func_owner.get(t)
                if owner and owner != name:
                    self.refs[owner].add(name)

        # .yy references (sprite of an object, parent, collisions, room instances, tilesets…)
        for name, a in self.assets.items():
            strings = set()
            _strings_in(a["data"], strings)
            for s in strings:
                if s in names and s != name:
                    self.refs[s].add(name)
            if a["kind"] == "room":
                self._room_instances(name, a["data"])

        # room order / first room
        self.room_order = []
        for node in p.yyp.data.get("RoomOrderNodes") or []:
            rid = node.get("roomId") or {}
            if rid.get("name"):
                self.room_order.append(rid["name"])

    def _room_instances(self, room, data):
        def walk(layers):
            for layer in layers or []:
                for inst in layer.get("instances") or []:
                    obj = (inst.get("objectId") or {}).get("name")
                    if obj:
                        self.room_instances[room][obj] += 1
                walk(layer.get("layers"))
        walk(data.get("layers"))

    def kind(self, name):
        return self.assets[name]["kind"]

    def of_kind(self, kind):
        return sorted(n for n, a in self.assets.items() if a["kind"] == kind)

    def unused(self):
        out = []
        for name, a in sorted(self.assets.items()):
            if a["kind"] in NEVER_UNUSED or a["kind"] == "other":
                continue
            if not self.refs.get(name):
                out.append(name)
        return out

    def sprite_thumb(self, name, size=48):
        a = self.assets.get(name)
        if not a or a["kind"] != "sprite":
            return None
        frames = a["data"].get("frames") or []
        if not frames:
            return None
        png = os.path.join(os.path.dirname(self.p.abs(a["path"])), "%s.png" % frames[0].get("name"))
        if not os.path.isfile(png):
            return None
        try:
            from PIL import Image
            im = Image.open(png).convert("RGBA")
            scale = max(1, size // max(im.size)) if max(im.size) < size else 1
            if scale > 1:
                im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            else:
                im.thumbnail((size, size))
            buf = io.BytesIO()
            im.save(buf, "PNG")
            data = buf.getvalue()
        except Exception:  # Pillow missing or unreadable image: embed the original file
            with open(png, "rb") as f:
                data = f.read()
            if len(data) > 200000:
                return None
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


# ---------------------------------------------------------------- HTML

CSS = """
:root{--bg:#f6f5f2;--panel:#fff;--ink:#1d1d1f;--muted:#6b6b73;--line:#e3e1dc;--accent:#2f6fde;--warn:#b5560d;
--ok:#1f8a4c;--chip:#efede8;--chk:#e8e6e1}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141417;--panel:#1c1c21;--ink:#ecebe8;
--muted:#9a99a3;--line:#2c2c33;--accent:#7aa7ff;--warn:#f0a35e;--ok:#5fcf8f;--chip:#26262d;--chk:#2a2a31}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.45 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{padding:28px 20px 8px;max-width:1180px;margin:auto}h1{margin:0 0 4px;font-size:26px}
.sub{color:var(--muted)}main{max-width:1180px;margin:auto;padding:0 20px 60px}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}.stat{background:var(--panel);border:1px solid var(--line);
border-radius:10px;padding:10px 14px;min-width:110px}.stat b{display:block;font-size:22px}.stat span{color:var(--muted);font-size:12px}
nav{position:sticky;top:0;background:var(--bg);padding:10px 0;z-index:2;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid var(--line)}
nav a{color:var(--ink);text-decoration:none;padding:5px 10px;border-radius:999px;background:var(--chip);font-size:13px}
input[type=search]{flex:1;min-width:180px;padding:7px 12px;border-radius:999px;border:1px solid var(--line);
background:var(--panel);color:var(--ink)}h2{margin:34px 0 12px;font-size:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px;display:flex;gap:12px}
.thumb{width:52px;height:52px;flex:none;border-radius:8px;display:grid;place-items:center;
background:repeating-conic-gradient(var(--chk) 0 25%,var(--panel) 0 50%) 0 0/12px 12px;image-rendering:pixelated}
.thumb img{max-width:48px;max-height:48px;image-rendering:pixelated}.thumb.none{color:var(--muted);font-size:11px}
.name{font-weight:600;word-break:break-all}.meta{color:var(--muted);font-size:12px;margin:2px 0 6px}
.chips{display:flex;flex-wrap:wrap;gap:4px}.chip{background:var(--chip);border-radius:6px;padding:1px 7px;font-size:12px}
.chip.warn{color:var(--warn)}.chip.ok{color:var(--ok)}
.tree ul{list-style:none;padding-left:18px;margin:0;border-left:1px dashed var(--line)}.tree>ul{border:0;padding:0}
.tree li{padding:3px 0}.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:500;font-size:12px}.note{color:var(--muted);font-size:12px;margin-top:8px}
.err{color:var(--warn)}.hide{display:none!important}
"""

JS = """
const q=document.getElementById('q');q.addEventListener('input',()=>{const v=q.value.toLowerCase();
document.querySelectorAll('[data-s]').forEach(e=>e.classList.toggle('hide',v&&!e.dataset.s.includes(v)))});
"""


def _e(s):
    return html.escape(str(s))


def build_html(scan, check_errors):
    p = scan.p
    objs, sprs, scrs, rooms = (scan.of_kind(k) for k in ("object", "sprite", "script", "room"))
    unused = scan.unused()
    title = os.path.splitext(os.path.basename(p.yyp_path))[0]
    out = ["<!doctype html><html lang=en><head><meta charset=utf-8>",
           "<meta name=viewport content='width=device-width,initial-scale=1'>",
           "<title>%s map</title><style>%s</style></head><body>" % (_e(title), CSS),
           "<header><h1>%s</h1><div class=sub>GameMaker project map · IDE %s · generated by gamemaker-kit</div>"
           % (_e(title), _e(p.ide_version or "unknown"))]
    stats = [("objects", len(objs)), ("sprites", len(sprs)), ("scripts", len(scrs)), ("rooms", len(rooms)),
             ("functions", sum(len(v) for v in scan.functions.values())),
             ("events", sum(len(scan.assets[o]["data"].get("eventList") or []) for o in objs)),
             ("unused", len(unused)), ("check errors", len(check_errors))]
    out.append("<div class=stats>" + "".join("<div class=stat><b>%d</b><span>%s</span></div>" % (v, k)
                                               for k, v in stats) + "</div></header><main>")
    out.append("<nav><a href=#objects>Objects</a><a href=#tree>Inheritance</a><a href=#rooms>Rooms</a>"
               "<a href=#sprites>Sprites</a><a href=#scripts>Scripts</a><a href=#unused>Unused</a>"
               "<a href=#health>Health</a><input id=q type=search placeholder='Filter by name…'></nav>")

    # objects
    out.append("<h2 id=objects>Objects</h2><div class=grid>")
    for o in objs:
        d = scan.assets[o]["data"]
        spr = (d.get("spriteId") or {}).get("name") if isinstance(d.get("spriteId"), dict) else None
        parent = (d.get("parentObjectId") or {}).get("name") if isinstance(d.get("parentObjectId"), dict) else None
        thumb = scan.sprite_thumb(spr) if spr else None
        evs = []
        for e in d.get("eventList") or []:
            other = (e.get("collisionObjectId") or {}).get("name") if isinstance(e.get("collisionObjectId"), dict) else None
            evs.append(event_name(e.get("eventType"), e.get("eventNum"), other))
        placed = sum(r.get(o, 0) for r in scan.room_instances.values())
        lines = sum(t.count("\n") + 1 for t in scan.gml.get(o, {}).values())
        meta = []
        if parent:
            meta.append("child of %s" % parent)
        if d.get("persistent"):
            meta.append("persistent")
        if d.get("visible") is False:
            meta.append("invisible")
        meta.append("%d lines" % lines)
        meta.append("placed %d×" % placed if placed else "not placed in rooms")
        out.append("<div class=card data-s='%s'><div class='thumb%s'>%s</div><div><div class=name>%s</div>"
                   "<div class=meta>%s</div><div class=chips>%s</div></div></div>" % (
                       _e(o.lower()), "" if thumb else " none",
                       "<img alt='' src='%s'>" % thumb if thumb else "no sprite", _e(o), _e(" · ".join(meta)),
                       "".join("<span class=chip>%s</span>" % _e(x) for x in evs) or
                       "<span class='chip warn'>no events</span>"))
    out.append("</div>")

    # inheritance
    children = defaultdict(list)
    roots = []
    for o in objs:
        d = scan.assets[o]["data"]
        parent = (d.get("parentObjectId") or {}).get("name") if isinstance(d.get("parentObjectId"), dict) else None
        (children[parent].append(o) if parent else roots.append(o))
    def tree(n):
        kids = sorted(children.get(n, []))
        return "<li>%s%s</li>" % (_e(n), "<ul>%s</ul>" % "".join(tree(k) for k in kids) if kids else "")
    with_kids = [r for r in roots if children.get(r)]
    out.append("<h2 id=tree>Inheritance</h2><div class='panel tree'>")
    out.append("<ul>%s</ul>" % "".join(tree(r) for r in sorted(with_kids)) if with_kids else
               "<div class=note>No parent/child objects yet.</div>")
    out.append("</div>")

    # rooms
    out.append("<h2 id=rooms>Rooms</h2><div class=panel><table><tr><th>#</th><th>Room</th><th>Size</th>"
               "<th>Instances</th></tr>")
    order = scan.room_order + [r for r in rooms if r not in scan.room_order]
    for i, r in enumerate(order):
        d = scan.assets.get(r, {}).get("data", {})
        rs = d.get("roomSettings") or {}
        inst = scan.room_instances.get(r, {})
        out.append("<tr data-s='%s'><td>%d</td><td class=name>%s%s</td><td>%s</td><td>%s</td></tr>" % (
            _e(r.lower()), i + 1, _e(r), " <span class='chip ok'>first</span>" if i == 0 else "",
            _e("%s×%s" % (rs.get("Width", "?"), rs.get("Height", "?"))),
            ", ".join("%s ×%d" % (_e(k), v) for k, v in sorted(inst.items())) or "<span class=note>empty</span>"))
    out.append("</table></div>")

    # sprites
    out.append("<h2 id=sprites>Sprites</h2><div class=grid>")
    for s in sprs:
        d = scan.assets[s]["data"]
        thumb = scan.sprite_thumb(s)
        users = sorted(scan.refs.get(s, []))
        out.append("<div class=card data-s='%s'><div class='thumb%s'>%s</div><div><div class=name>%s</div>"
                   "<div class=meta>%s×%s · %d frame%s</div><div class=chips>%s</div></div></div>" % (
                       _e(s.lower()), "" if thumb else " none", "<img alt='' src='%s'>" % thumb if thumb else "?",
                       _e(s), d.get("width", "?"), d.get("height", "?"), len(d.get("frames") or []),
                       "" if len(d.get("frames") or []) == 1 else "s",
                       "".join("<span class=chip>%s</span>" % _e(u) for u in users[:6]) or
                       "<span class='chip warn'>unused</span>"))
    out.append("</div>")

    # scripts
    out.append("<h2 id=scripts>Scripts</h2><div class=panel><table><tr><th>Script</th><th>Functions</th>"
               "<th>Used by</th></tr>")
    for s in scrs:
        users = sorted(scan.refs.get(s, []))
        out.append("<tr data-s='%s'><td class=name>%s</td><td>%s</td><td>%s</td></tr>" % (
            _e(s.lower()), _e(s), ", ".join(_e(f) for f in scan.functions.get(s, [])) or "<span class=note>—</span>",
            ", ".join(_e(u) for u in users[:12]) or "<span class=err>nothing references these functions</span>"))
    out.append("</table></div>")

    # unused
    out.append("<h2 id=unused>Possibly unused</h2><div class=panel>")
    if unused:
        out.append("<div class=chips>%s</div>" % "".join(
            "<span class='chip warn' data-s='%s'>%s · %s</span>" % (_e(u.lower()), _e(u), _e(scan.kind(u)))
            for u in unused))
        out.append("<div class=note>Not referenced by any code, object, room or other asset. Assets looked up "
                   "by a built name (e.g. <code>asset_get_index(\"spr_\" + name)</code>) look unused here — check "
                   "before removing.</div>")
    else:
        out.append("<div class=note>Every asset is referenced somewhere.</div>")
    out.append("</div>")

    # health
    out.append("<h2 id=health>Health</h2><div class=panel>")
    if check_errors:
        out.append("<ul>%s</ul>" % "".join("<li class=err>%s</li>" % _e(e) for e in check_errors))
    else:
        out.append("<div class=note>check_project.py found no errors.</div>")
    out.append("</div></main><script>%s</script></body></html>" % JS)
    return "".join(out)


def cmd_map(p, args):
    import check_project
    scan = Scan(p)
    rep, _ = check_project.check(p.yyp_path)
    page = build_html(scan, rep.errors)
    target = args.output or os.path.join(p.root, "project-map.html")
    if args.dry_run:
        print("would write %s" % target)
        return
    with open(target, "w", encoding="utf-8") as f:
        f.write(page)
    print("map written: %s (%d objects, %d sprites, %d unused)" % (
        target, len(scan.of_kind("object")), len(scan.of_kind("sprite")), len(scan.unused())))


def cmd_unused(p, args):
    scan = Scan(p)
    unused = scan.unused()
    if not args.remove:
        if not unused:
            print("no unused assets found")
            return
        print("possibly unused (%d):" % len(unused))
        for u in unused:
            print("  %-32s %s" % (u, scan.kind(u)))
        print("note: assets found by a built name (asset_get_index(\"spr_\" + name)) look unused here; check "
              "before removing. Remove with: unused <project> --remove name1,name2")
        return
    targets = unused if args.remove == "all" else [n.strip() for n in args.remove.split(",") if n.strip()]
    for t in targets:
        if t not in scan.assets:
            raise Refused("%s is not an asset" % t)
        if t not in unused:
            raise Refused("%s is referenced by %s; not removing" % (t, ", ".join(sorted(scan.refs[t]))))
    trash = os.path.join(p.root, "_gmkit_removed")
    for t in targets:
        p.unregister(t)
        folder = os.path.dirname(p.abs(scan.assets[t]["path"]))
        p.moves.append((folder, os.path.join(trash, scan.assets[t]["path"].split("/")[0], t)))
    print("removing %d asset(s) from the project; their folders go to _gmkit_removed/ so nothing is lost"
          % len(targets))


def register_cli(common):
    sp = common("map", help="write an HTML map of the project")
    sp.add_argument("-o", "--output")
    sp = common("unused", help="list (or remove) assets nothing references")
    sp.add_argument("--remove")
    return {"map": cmd_map, "unused": cmd_unused}
