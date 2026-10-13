#!/usr/bin/env python3
"""Template-based asset scaffolding for GameMaker projects (2.3+ JSON format).

Every new asset is cloned from an existing asset of the same type in the same
project, so the output always matches the project's IDE version. Nothing is
written unless the clone can be re-serialised in exactly the project's own
style (checked by a round trip on the template).

Commands (run with -h for options)
  info             <project>
  new-object       <project> <name> [--events Create,Step,Draw,DrawGUI,Alarm0,Collision:obj_wall,...]
                                    [--sprite spr_x] [--parent obj_base] [--folder F] [--persistent]
  add-event        <project> <object> <event> [<event> ...]
  new-script       <project> <name>
  new-sprite       <project> <name> (--frames a.png ... | --sheet s.png --frame-w W --frame-h H)
                                    [--origin preset|X,Y] [--fps N]
  starter          <project> [--genre topdown|platformer] [--prefix kit_]       (gm_starter.py)
  add-system       <project> input juice save level camera fade                 (gm_starter.py)
  import-aseprite  <project> export.json [--prefix spr_x]                       (gm_import.py)
  import-folder    <project> folder/ [--fps N]                                  (gm_import.py)
  rename           <project> <old> <new>                                        (gm_refactor.py)
  map              <project> [-o project-map.html]                              (gm_map.py)
  unused           <project> [--remove a,b | all]                               (gm_map.py)
  extract-strings  <project> [--langs tr] [--apply]                             (gm_lang.py)
  build-lang       <project>                                                    (gm_lang.py)
Common flag: --dry-run (print what would change, write nothing)

Exit code 0 on success, 1 on a refused change (nothing written), 2 on usage errors.
Python 3.8+, standard library only (new-sprite needs Pillow).
"""
import argparse
import copy
import json
import os
import re
import sys
import uuid

# ---------------------------------------------------------------- parsing


def strip_trailing_commas(text):
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            out.append(c)
        elif c == ",":
            j = i + 1
            while j < n and text[j] in " \t\r\n":
                j += 1
            if not (j < n and text[j] in "}]"):
                out.append(c)
        else:
            out.append(c)
        i += 1
    return "".join(out)


class Refused(Exception):
    """A change was refused; nothing has been written."""


class YYFile:
    """A .yy/.yyp file with its original text, parsed data and detected style."""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            raw = f.read()
        self.bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        self.newline = "\r\n" if "\r\n" in text else "\n"
        self.text = text.replace("\r\n", "\n")
        self.data = json.loads(strip_trailing_commas(self.text))
        self.style = None

    def matching_styles(self):
        target = self.text.rstrip("\n")
        return [s for s in STYLES if gm_dumps(self.data, s) == target]

    def detect_style(self, peers=()):
        """Find writer settings that reproduce this file (and its peers) byte for byte.

        Several layouts can reproduce a file that has empty lists; peers of the same asset
        type narrow that down. If the remaining layouts would still write new data
        differently, render() refuses instead of guessing."""
        styles = self.matching_styles()
        if not styles:
            raise Refused(
                "%s uses a layout this script cannot reproduce exactly, so it will not write files "
                "based on it. Create the asset in the IDE, or edit by hand following the skill."
                % os.path.relpath(self.path))
        for peer in peers:
            narrowed = [s for s in styles if s in peer.matching_styles()]
            if narrowed:
                styles = narrowed
        self.style = styles
        return styles[0]

    def render(self, data):
        if self.style is None:
            self.detect_style()
        outputs = {gm_dumps(data, s) for s in self.style}
        if len(outputs) != 1:
            raise Refused(
                "the project's file layout is ambiguous for this change (the template has empty lists). "
                "Pass --template with an asset that already has the same kind of content (e.g. an object "
                "with events), or add one in the IDE first.")
        trailing = "\n" if self.text.endswith("\n") else ""
        return (outputs.pop() + trailing).replace("\n", self.newline)


# ---------------------------------------------------------------- writing in GameMaker's style
# style = (dict_depth, list_depth, list_items_multiline)
#   a dict is written over several lines when it sits shallower than dict_depth, a list when it
#   sits shallower than list_depth; with list_items_multiline=False the elements of a list are
#   always written on one line each.
STYLES = [(d, l, a) for d in (1, 2, 3, 4, 6, 99) for l in (1, 2, 3, 4, 6, 99) for a in (False, True)]


def _scalar(v):
    return json.dumps(v, ensure_ascii=False)


def _inline(v):
    if isinstance(v, dict):
        if not v:
            return "{}"
        return "{" + "".join("%s:%s," % (_scalar(k), _inline(x)) for k, x in v.items()) + "}"
    if isinstance(v, list):
        if not v:
            return "[]"
        return "[" + "".join("%s," % _inline(x) for x in v) + "]"
    return _scalar(v)


def gm_dumps(v, style, depth=0, in_array=False):
    dict_depth, list_depth, items_multiline = style
    limit = dict_depth if isinstance(v, dict) else list_depth
    multiline = depth < limit and not (in_array and not items_multiline)
    if not isinstance(v, (dict, list)) or not v or not multiline:
        return _inline(v)
    pad = "  " * (depth + 1)
    lines = []
    if isinstance(v, dict):
        for k, x in v.items():
            lines.append("%s%s:%s," % (pad, _scalar(k), gm_dumps(x, style, depth + 1)))
        return "{\n" + "\n".join(lines) + "\n" + "  " * depth + "}"
    for x in v:
        lines.append("%s%s," % (pad, gm_dumps(x, style, depth + 1, in_array=True)))
    return "[\n" + "\n".join(lines) + "\n" + "  " * depth + "]"


# ---------------------------------------------------------------- project access

ASSET_DIRS = {"object": "objects", "sprite": "sprites", "script": "scripts", "room": "rooms"}
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
GUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class Project:
    def __init__(self, arg):
        if os.path.isfile(arg) and arg.endswith(".yyp"):
            self.yyp_path = arg
        elif os.path.isdir(arg):
            found = [f for f in os.listdir(arg) if f.endswith(".yyp")]
            if len(found) != 1:
                raise Refused("expected exactly one .yyp in %s, found %d" % (arg, len(found)))
            self.yyp_path = os.path.join(arg, found[0])
        else:
            raise Refused("no GameMaker project at %s" % arg)
        self.root = os.path.dirname(os.path.abspath(self.yyp_path))
        self.yyp = YYFile(self.yyp_path)
        self.resources = []
        for entry in self.yyp.data.get("resources") or []:
            ref = entry.get("id", entry)
            if isinstance(ref, dict) and ref.get("name") and ref.get("path"):
                self.resources.append((ref["name"], ref["path"]))
        self.names = {n for n, _ in self.resources}
        self.writes = []  # (path, content-or-bytes)
        self.moves = []   # (src, dst) applied after all writes

    @property
    def ide_version(self):
        return (self.yyp.data.get("MetaData") or {}).get("IDEVersion")

    def abs(self, rel):
        return os.path.join(self.root, rel)

    def assets_of(self, kind):
        prefix = ASSET_DIRS[kind] + "/"
        return [(n, p) for n, p in self.resources if p.startswith(prefix)]

    def load(self, name):
        for n, p in self.resources:
            if n == name:
                return YYFile(self.abs(p))
        raise Refused("%s is not an asset in this project" % name)

    def path_of(self, name):
        for n, p in self.resources:
            if n == name:
                return p
        return None

    def peers(self, kind, exclude, limit=25):
        out = []
        for n, p in self.assets_of(kind):
            if n == exclude:
                continue
            try:
                out.append(YYFile(self.abs(p)))
            except (ValueError, OSError):
                continue
            if len(out) >= limit:
                break
        return out

    def pick_template(self, kind, requested=None, prefer=None):
        tpl = self._pick_template(kind, requested, prefer)
        tpl.detect_style(self.peers(kind, tpl.data.get("name")))
        return tpl

    def _pick_template(self, kind, requested=None, prefer=None):
        if requested:
            if requested not in self.names:
                raise Refused("template %s does not exist" % requested)
            return self.load(requested)
        candidates = self.assets_of(kind)
        if not candidates:
            raise Refused(
                "this project has no %s yet. Create one empty %s in the GameMaker IDE, save, and run "
                "this again - its file becomes the template." % (kind, kind))
        loaded = []
        for n, p in candidates:
            try:
                f = YYFile(self.abs(p))
                f.detect_style()
                loaded.append(f)
            except (Refused, ValueError, OSError):
                continue
        if not loaded:
            raise Refused("none of this project's %ss can be reproduced exactly; edit by hand" % kind)
        if prefer:
            loaded.sort(key=prefer)
        return loaded[0]

    def check_new_name(self, name):
        if not NAME_RE.match(name):
            raise Refused("%r is not a valid asset name (letters, digits, underscore; max 64)" % name)
        if name in self.names:
            raise Refused("an asset named %s already exists" % name)

    def folder_ref(self, folder, fallback):
        if not folder:
            return fallback
        for fo in self.yyp.data.get("Folders") or []:
            path = fo.get("folderPath") or fo.get("path")
            if folder in (fo.get("name"), path, path and path[len("folders/"):-len(".yy")]):
                ref = copy.deepcopy(fallback) if isinstance(fallback, dict) else {}
                ref["name"] = fo.get("name")
                ref["path"] = path
                return ref
        names = sorted(fo.get("name") for fo in self.yyp.data.get("Folders") or [])
        raise Refused("folder %r not found. Existing folders: %s" % (folder, ", ".join(names)))

    def asset_ref(self, name, like):
        path = self.path_of(name)
        if not path:
            raise Refused("%s does not exist in this project" % name)
        ref = copy.deepcopy(like) if isinstance(like, dict) else {}
        ref["name"] = name
        ref["path"] = path
        return ref

    def register(self, name, path, template_name):
        """Insert a resources line into the .yyp, cloned from the template's line."""
        lines = self.yyp.text.split("\n")
        try:
            start = next(i for i, l in enumerate(lines) if l.strip().startswith('"resources":['))
        except StopIteration:
            raise Refused("could not find the resources list in the .yyp")
        end = start + 1
        while end < len(lines) and not lines[end].strip().startswith("]"):
            end += 1
        tpl_line = None
        for i in range(start + 1, end):
            if '"name":%s' % json.dumps(template_name) in lines[i].replace(" ", ""):
                tpl_line = lines[i]
        if tpl_line is None or lines[start].rstrip().endswith("[]"):
            raise Refused("the .yyp lists resources in a layout this script cannot edit safely")
        tpl_path = self.path_of(template_name)
        new_line = tpl_line.replace(json.dumps(tpl_path), json.dumps(path)).replace(
            json.dumps(template_name), json.dumps(name))
        pos = end
        for i in range(start + 1, end):
            m = re.search(r'"name"\s*:\s*"([^"]+)"', lines[i])
            if m and m.group(1).lower() > name.lower():
                pos = i
                break
        lines.insert(pos, new_line)
        text = "\n".join(lines)
        data = json.loads(strip_trailing_commas(text))
        found = [e for e in data.get("resources", []) if e.get("id", e).get("name") == name]
        if len(found) != 1 or found[0].get("id", found[0]).get("path") != path:
            raise Refused("registering %s in the .yyp did not produce the expected entry" % name)
        self.yyp.text = text
        self.yyp.data = data
        self.resources.append((name, path))
        self.names.add(name)
        self.writes = [w for w in self.writes if w[0] != self.yyp_path]
        self.queue(self.yyp_path, text.replace("\n", self.yyp.newline), bom=self.yyp.bom)

    def unregister(self, name):
        """Remove an asset's line from the .yyp resources list."""
        lines = self.yyp.text.split("\n")
        hits = [i for i, l in enumerate(lines)
                if re.search(r'"name"\s*:\s*%s' % re.escape(json.dumps(name)), l) and '"path"' in l]
        if len(hits) != 1:
            raise Refused("could not find exactly one .yyp line for %s" % name)
        del lines[hits[0]]
        text = "\n".join(lines)
        data = json.loads(strip_trailing_commas(text))
        if any(e.get("id", e).get("name") == name for e in data.get("resources", [])):
            raise Refused("removing %s from the .yyp did not work" % name)
        self.yyp.text, self.yyp.data = text, data
        self.resources = [(n, pth) for n, pth in self.resources if n != name]
        self.names.discard(name)
        self.writes = [w for w in self.writes if w[0] != self.yyp_path]
        self.queue(self.yyp_path, text.replace("\n", self.yyp.newline), bom=self.yyp.bom)

    def queue(self, path, content, bom=False):
        if isinstance(content, str):
            content = (b"\xef\xbb\xbf" if bom else b"") + content.encode("utf-8")
        self.writes.append((path, content))

    def commit(self, dry_run):
        """Write everything to temporary files first, then move them into place with the .yyp last,
        so an interrupted run leaves at most unregistered (harmless) files behind."""
        plan = [(p, c, os.path.exists(p)) for p, c in self.writes]
        plan.sort(key=lambda item: item[0] == self.yyp_path)
        report = ["%s %s" % ("would write" if dry_run else ("update" if ex else "create"),
                             os.path.relpath(p, self.root)) for p, _, ex in plan]
        if not dry_run:
            temps = []
            try:
                for path, content, _ in plan:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    tmp = path + ".gmkit.tmp"
                    with open(tmp, "wb") as f:
                        f.write(content)
                    temps.append((tmp, path))
            except OSError:
                for tmp, _ in temps:
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
                raise
            for tmp, path in temps:
                os.replace(tmp, path)
            for path, content, _ in plan:
                with open(path, "rb") as f:
                    if f.read() != content:
                        raise SystemExit("ERROR: %s did not keep the written content (synced folder?)"
                                         % os.path.relpath(path, self.root))
        for src, dst in self.moves:
            report.append("%s %s -> %s" % ("would move" if dry_run else "move",
                                           os.path.relpath(src, self.root), os.path.relpath(dst, self.root)))
            if dry_run:
                continue
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                os.replace(src, dst)
            except OSError as e:
                report.append("  could not move (%s); the folder stays where it was and is no longer "
                              "registered - delete it yourself" % e)
        try:
            print("\n".join(report))
        except BrokenPipeError:
            pass


# ---------------------------------------------------------------- renaming helpers


def rename_everywhere(data, old, new):
    """Replace the asset name in name fields and path segments throughout a structure."""
    if isinstance(data, dict):
        return {k: rename_everywhere(v, old, new) for k, v in data.items()}
    if isinstance(data, list):
        return [rename_everywhere(v, old, new) for v in data]
    if isinstance(data, str):
        if data == old:
            return new
        if "/" in data:
            parts = data.split("/")
            parts = [new if p == old else (new + ".yy" if p == old + ".yy" else p) for p in parts]
            return "/".join(parts)
    return data


def replace_strings(data, mapping):
    if isinstance(data, dict):
        return {k: replace_strings(v, mapping) for k, v in data.items()}
    if isinstance(data, list):
        return [replace_strings(v, mapping) for v in data]
    if isinstance(data, str):
        return mapping.get(data, data)
    return data


def contains_string(data, s):
    if isinstance(data, dict):
        return any(contains_string(v, s) for v in data.values())
    if isinstance(data, list):
        return any(contains_string(v, s) for v in data)
    return data == s


def set_name(data, name):
    data["name"] = name
    if "%Name" in data:
        data["%Name"] = name


# ---------------------------------------------------------------- events

EVENT_ALIASES = {
    "create": (0, 0), "destroy": (1, 0), "cleanup": (12, 0), "precreate": (14, 0),
    "step": (3, 0), "beginstep": (3, 1), "endstep": (3, 2),
    "draw": (8, 0), "drawgui": (8, 64), "drawbegin": (8, 72), "drawend": (8, 73),
    "drawguibegin": (8, 74), "drawguiend": (8, 75), "predraw": (8, 76), "postdraw": (8, 77),
    "windowresize": (8, 65),
    "gamestart": (7, 2), "gameend": (7, 3), "roomstart": (7, 4), "roomend": (7, 5),
    "animationend": (7, 7), "outsideroom": (7, 0), "intersectboundary": (7, 1),
    "asyncsystem": (7, 75), "asynchttp": (7, 62), "asyncsaveload": (7, 72), "asyncsteam": (7, 69),
    "asyncdialog": (7, 63), "asyncnetworking": (7, 68), "asyncsocial": (7, 70),
}
PREFIX = {0: "Create", 1: "Destroy", 2: "Alarm", 3: "Step", 4: "Collision", 5: "Keyboard", 6: "Mouse",
          7: "Other", 8: "Draw", 9: "KeyPress", 10: "KeyRelease", 12: "CleanUp", 13: "Gesture",
          14: "PreCreate"}
KEY_NAMES = {"left": 37, "up": 38, "right": 39, "down": 40, "space": 32, "enter": 13, "escape": 27,
             "shift": 16, "control": 17, "alt": 18, "tab": 9, "backspace": 8}


def parse_event(spec):
    """'Step' -> (3,0,None); 'Alarm2' -> (2,2,None); 'Collision:obj_wall' -> (4,0,'obj_wall')."""
    s = spec.strip()
    low = s.lower().replace(" ", "").replace("_", "")
    if low.startswith("collision:"):
        return 4, 0, s.split(":", 1)[1].strip()
    for prefix, et in (("keypress:", 9), ("keyrelease:", 10), ("keyboard:", 5)):
        if low.startswith(prefix):
            key = s.split(":", 1)[1].strip()
            if len(key) == 1 and key.isalnum():
                return et, ord(key.upper()), None
            if key.lower() in KEY_NAMES:
                return et, KEY_NAMES[key.lower()], None
            if key.isdigit():
                return et, int(key), None
            raise Refused("unknown key %r in %s" % (key, spec))
    m = re.match(r"^alarm(\d+)$", low)
    if m and int(m.group(1)) <= 11:
        return 2, int(m.group(1)), None
    m = re.match(r"^user(?:event)?(\d+)$", low)
    if m and int(m.group(1)) <= 15:
        return 7, 10 + int(m.group(1)), None
    if low in EVENT_ALIASES:
        et, en = EVENT_ALIASES[low]
        return et, en, None
    raise Refused("unknown event %r. Use e.g. Create, Step, EndStep, Draw, DrawGUI, Alarm0, User0, "
                  "RoomStart, Collision:obj_wall, KeyPress:A" % spec)


def event_filename(et, en, other):
    if et == 4:
        return "Collision_%s.gml" % other
    return "%s_%d.gml" % (PREFIX[et], en)


def event_template(project, obj_file):
    """An eventList entry to clone: from the object itself, or from any object in the project."""
    events = obj_file.data.get("eventList") or []
    if events:
        return events[0]
    for name, path in project.assets_of("object"):
        try:
            evs = YYFile(project.abs(path)).data.get("eventList") or []
        except (ValueError, OSError):
            continue
        if evs:
            return evs[0]
    raise Refused("no object in this project has an event yet, so the event format is unknown. Add one "
                  "event to any object in the IDE and run this again.")


def build_event(project, tpl_event, et, en, other):
    ev = copy.deepcopy(tpl_event)
    ev["eventType"] = et
    ev["eventNum"] = en
    if "collisionObjectId" in ev:
        if et == 4:
            ev["collisionObjectId"] = project.asset_ref(other, {"name": "", "path": ""})
        else:
            ev["collisionObjectId"] = None
    elif et == 4:
        raise Refused("this project's event format has no collisionObjectId field; add the collision "
                      "event in the IDE")
    return ev


def add_events_to(project, obj_name, obj_dir_rel, data, specs, tpl_event, code=None):
    """Append events to an object's data and queue their .gml files.
    code: optional {spec_or_filename: gml text}."""
    code = code or {}
    existing = {(e.get("eventType"), e.get("eventNum"),
                 (e.get("collisionObjectId") or {}).get("name") if isinstance(e.get("collisionObjectId"), dict) else None)
                for e in data.get("eventList") or []}
    new_files = []
    for spec in specs:
        et, en, other = parse_event(spec)
        if et == 4 and other not in project.names:
            raise Refused("collision object %s does not exist" % other)
        if (et, en, other) in existing:
            raise Refused("%s already has a %s event" % (obj_name, spec))
        data.setdefault("eventList", []).append(build_event(project, tpl_event, et, en, other))
        existing.add((et, en, other))
        fname = event_filename(et, en, other)
        new_files.append(fname)
        body = code.get(spec, code.get(fname, "/// @description %s\n\n" % spec.strip()))
        project.queue(project.abs(os.path.join(obj_dir_rel, fname)), body)
    return new_files


# ---------------------------------------------------------------- library API (used by the commands
# below and by the other gm_*.py modules)

def _object_template(p, requested=None):
    return p.pick_template("object", requested,
                           prefer=lambda f: (0 if f.data.get("eventList") else 1,
                                             len(f.data.get("eventList") or [])))


def create_object(p, name, events=(), code=None, sprite=None, parent=None, folder=None,
                  persistent=False, visible=True, template=None):
    p.check_new_name(name)
    tpl = _object_template(p, template)
    tpl_event = event_template(p, tpl) if events else None
    old = tpl.data["name"]
    data = rename_everywhere(copy.deepcopy(tpl.data), old, name)
    set_name(data, name)
    data["eventList"] = []
    if "spriteId" in data:
        data["spriteId"] = p.asset_ref(sprite, tpl.data.get("spriteId") or {}) if sprite else None
    elif sprite:
        raise Refused("this project's object format has no spriteId field")
    if "spriteMaskId" in data:
        data["spriteMaskId"] = None
    if "parentObjectId" in data:
        data["parentObjectId"] = p.asset_ref(parent, tpl.data.get("parentObjectId") or {}) if parent else None
    elif parent:
        raise Refused("this project's object format has no parentObjectId field")
    if "persistent" in data:
        data["persistent"] = bool(persistent)
    if "visible" in data:
        data["visible"] = bool(visible)
    for key in ("properties", "overriddenProperties"):
        if isinstance(data.get(key), list):
            data[key] = []
    if "parent" in data:
        data["parent"] = p.folder_ref(folder, tpl.data.get("parent"))
    dir_rel = "objects/%s" % name
    add_events_to(p, name, dir_rel, data, list(events), tpl_event, code)
    p.queue(p.abs("%s/%s.yy" % (dir_rel, name)), tpl.render(data), bom=tpl.bom)
    p.register(name, "%s/%s.yy" % (dir_rel, name), old)
    return old


def add_events(p, obj, specs, code=None):
    f = p.load(obj)
    f.detect_style(p.peers("object", obj))
    path = p.path_of(obj)
    if not path.startswith("objects/"):
        raise Refused("%s is not an object" % obj)
    data = copy.deepcopy(f.data)
    add_events_to(p, obj, os.path.dirname(path), data, specs, event_template(p, f), code)
    p.queue(f.path, f.render(data), bom=f.bom)


def create_script(p, name, code=None, folder=None, template=None):
    p.check_new_name(name)
    tpl = p.pick_template("script", template)
    old = tpl.data["name"]
    data = rename_everywhere(copy.deepcopy(tpl.data), old, name)
    set_name(data, name)
    if "parent" in data:
        data["parent"] = p.folder_ref(folder, tpl.data.get("parent"))
    dir_rel = "scripts/%s" % name
    p.queue(p.abs("%s/%s.yy" % (dir_rel, name)), tpl.render(data), bom=tpl.bom)
    p.queue(p.abs("%s/%s.gml" % (dir_rel, name)), code if code is not None else (
        "/// Functions declared here are global and available from game start.\n\n"
        "function %s() {\n\n}\n" % name))
    p.register(name, "%s/%s.yy" % (dir_rel, name), old)
    return old


ORIGINS = {"top-left": 0, "top-centre": 1, "top-right": 2, "middle-left": 3, "middle-centre": 4,
           "middle-right": 5, "bottom-left": 6, "bottom-centre": 7, "bottom-right": 8}


def _find_keyframes(seq):
    for track in seq.get("tracks") or []:
        kfs = track.get("keyframes")
        if isinstance(kfs, dict) and isinstance(kfs.get("Keyframes"), list):
            return kfs["Keyframes"]
    return None


def need_pillow():
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        raise Refused("this command needs Pillow: python3 -m pip install Pillow")


def slice_sheet(sheet, w, h, count=None):
    imgs = []
    for r in range(sheet.height // h):
        for c in range(sheet.width // w):
            imgs.append(sheet.crop((c * w, r * h, c * w + w, r * h + h)))
    if count:
        return imgs[:count]
    while imgs and imgs[-1].getbbox() is None:
        imgs.pop()  # drop empty cells at the end of the sheet
    return imgs


def _sprite_template(p, requested=None):
    def usable(f):
        return 0 if len(f.data.get("layers") or []) == 1 and f.data.get("frames") else 1
    tpl = p.pick_template("sprite", requested, prefer=usable)
    t = tpl.data
    frames, layers = t.get("frames") or [], t.get("layers") or []
    seq = t.get("sequence")
    if not frames or len(layers) != 1 or not isinstance(seq, dict):
        raise Refused("template %s must have at least one frame and exactly one layer" % t["name"])
    kfs = _find_keyframes(seq)
    if not kfs:
        raise Refused("template %s has no sprite-frame keyframes in its sequence" % t["name"])
    f0, l0, k0 = frames[0].get("name"), layers[0].get("name"), kfs[0].get("id")
    for g in (f0, l0, k0):
        if not (isinstance(g, str) and GUID_RE.match(g)):
            raise Refused("template %s uses an id format this script does not recognise" % t["name"])
    if not contains_string(kfs[0], f0):
        raise Refused("template %s's first keyframe does not point at its first frame" % t["name"])
    tdir = os.path.dirname(tpl.path)
    if not (os.path.isfile(os.path.join(tdir, f0 + ".png")) and
            os.path.isfile(os.path.join(tdir, "layers", f0, l0 + ".png"))):
        raise Refused("template %s's image files are not laid out as <frame>.png and "
                      "layers/<frame>/<layer>.png" % t["name"])
    return tpl


def create_sprite(p, name, imgs, origin="middle-centre", folder=None, template=None, fps=None):
    """imgs: list of same-size PIL RGBA images. fps: playback speed in frames per second (optional)."""
    import io
    p.check_new_name(name)
    if not imgs:
        raise Refused("%s: no frames" % name)
    w, h = imgs[0].size
    if any(i.size != (w, h) for i in imgs):
        raise Refused("%s: all frames must have the same size" % name)
    tpl = _sprite_template(p, template)
    t = tpl.data
    old = t["name"]
    frames, layers = t["frames"], t["layers"]
    kfs = _find_keyframes(t["sequence"])
    f0, l0, k0 = frames[0]["name"], layers[0]["name"], kfs[0]["id"]

    data = copy.deepcopy(t)
    layer_id = str(uuid.uuid4())
    new_frames, new_kfs, frame_ids = [], [], []
    for i in range(len(imgs)):
        fid = str(uuid.uuid4())
        frame_ids.append(fid)
        new_frames.append(replace_strings(copy.deepcopy(frames[0]), {f0: fid, l0: layer_id}))
        kf = replace_strings(copy.deepcopy(kfs[0]), {f0: fid, k0: str(uuid.uuid4())})
        if "Key" in kf:
            kf["Key"] = float(i)
        new_kfs.append(kf)
    data["frames"] = new_frames
    data["layers"] = [replace_strings(copy.deepcopy(layers[0]), {l0: layer_id})]
    _find_keyframes(data["sequence"])[:] = new_kfs
    data["sequence"]["length"] = float(len(imgs))
    data = rename_everywhere(data, old, name)
    set_name(data, name)
    if isinstance(data.get("sequence"), dict) and data["sequence"].get("name") == name:
        set_name(data["sequence"], name)
    for g in [fr.get("name") for fr in frames] + [l0] + [k.get("id") for k in kfs]:
        if g and contains_string(data, g):
            raise Refused("a template id survived the copy; refusing to write a sprite that shares ids")
    data["width"], data["height"] = w, h
    for k, v in (("bbox_left", 0), ("bbox_top", 0), ("bbox_right", w - 1), ("bbox_bottom", h - 1)):
        if k in data:
            data[k] = v
    origin = origin or "middle-centre"
    if origin in ORIGINS:
        code = ORIGINS[origin]
        ox = {0: 0, 1: w // 2, 2: w}[code % 3]
        oy = {0: 0, 1: h // 2, 2: h}[code // 3]
    else:
        try:
            ox, oy = [int(v) for v in origin.split(",")]
        except ValueError:
            raise Refused("origin must be a preset (%s) or X,Y" % ", ".join(ORIGINS))
        code = 9
    if "origin" in data:
        data["origin"] = code
    if "xorigin" in data["sequence"]:
        data["sequence"]["xorigin"], data["sequence"]["yorigin"] = ox, oy
    seq = data["sequence"]
    if fps and "playbackSpeed" in seq:
        if seq.get("playbackSpeedType", 0) == 0:          # 0 = frames per second
            seq["playbackSpeed"] = float(round(fps, 2))
        else:
            print("note: %s uses frames-per-game-frame playback; fps from the import was not applied" % name)
    if "parent" in data:
        data["parent"] = p.folder_ref(folder, t.get("parent"))

    dir_rel = "sprites/%s" % name
    p.queue(p.abs("%s/%s.yy" % (dir_rel, name)), tpl.render(data), bom=tpl.bom)
    for fid, img in zip(frame_ids, imgs):
        buf = io.BytesIO()
        img.save(buf, "PNG")
        png = buf.getvalue()
        p.queue(p.abs("%s/%s.png" % (dir_rel, fid)), png)
        p.queue(p.abs("%s/layers/%s/%s.png" % (dir_rel, fid, layer_id)), png)
    p.register(name, "%s/%s.yy" % (dir_rel, name), old)
    return old


# ---------------------------------------------------------------- basic commands


def cmd_info(p, args):
    print("Project: %s" % os.path.basename(p.yyp_path))
    print("IDE version: %s" % (p.ide_version or "unknown"))
    for kind in ("object", "sprite", "script", "room"):
        assets = p.assets_of(kind)
        ok = 0
        for n, path in assets:
            try:
                YYFile(p.abs(path)).detect_style()
                ok += 1
            except (Refused, ValueError, OSError):
                pass
        print("%-7s %3d (%d usable as templates)" % (kind + "s", len(assets), ok))
    try:
        print("Project file style: %s" % (p.yyp.detect_style(),))
    except Refused as e:
        print("Project file style: not reproducible (%s)" % e)


def cmd_new_object(p, args):
    old = create_object(p, args.name, args.events or [], sprite=args.sprite, parent=args.parent,
                        folder=args.folder, persistent=args.persistent, visible=not args.invisible,
                        template=args.template)
    print("template: %s" % old)
    if not args.sprite:
        print("note: no sprite set - the object will be invisible in the Room Editor")


def cmd_add_event(p, args):
    add_events(p, args.object, args.events)


def cmd_new_script(p, args):
    print("template: %s" % create_script(p, args.name, folder=args.folder, template=args.template))


def cmd_new_sprite(p, args):
    need_pillow()
    from PIL import Image
    if args.frames:
        imgs = [Image.open(f).convert("RGBA") for f in args.frames]
    else:
        imgs = slice_sheet(Image.open(args.sheet).convert("RGBA"), args.frame_w, args.frame_h, args.count)
    old = create_sprite(p, args.name, imgs, args.origin, args.folder, args.template, args.fps)
    print("template: %s  frames: %d  size: %dx%d  origin: %s" % (
        old, len(imgs), imgs[0].size[0], imgs[0].size[1], args.origin or "middle-centre"))
    print("note: check origin and collision mask in the Sprite Editor")


# ---------------------------------------------------------------- CLI


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(name, **kw):
        sp = sub.add_parser(name, **kw)
        sp.add_argument("project")
        sp.add_argument("--dry-run", action="store_true")
        return sp

    common("info")
    sp = common("new-object")
    sp.add_argument("name")
    sp.add_argument("--events", type=lambda s: [x for x in s.split(",") if x.strip()])
    sp.add_argument("--sprite")
    sp.add_argument("--parent")
    sp.add_argument("--folder")
    sp.add_argument("--template")
    sp.add_argument("--persistent", action="store_true")
    sp.add_argument("--invisible", action="store_true")
    sp = common("add-event")
    sp.add_argument("object")
    sp.add_argument("events", nargs="+")
    sp = common("new-script")
    sp.add_argument("name")
    sp.add_argument("--folder")
    sp.add_argument("--template")
    sp = common("new-sprite")
    sp.add_argument("name")
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--frames", nargs="+")
    g.add_argument("--sheet")
    sp.add_argument("--frame-w", type=int)
    sp.add_argument("--frame-h", type=int)
    sp.add_argument("--count", type=int)
    sp.add_argument("--origin")
    sp.add_argument("--fps", type=float)
    sp.add_argument("--folder")
    sp.add_argument("--template")

    # extension modules register their own subcommands
    handlers = {"info": cmd_info, "new-object": cmd_new_object, "add-event": cmd_add_event,
                "new-script": cmd_new_script, "new-sprite": cmd_new_sprite}
    for modname in ("gm_starter", "gm_import", "gm_refactor", "gm_map", "gm_lang"):
        try:
            mod = __import__(modname)
        except ImportError as e:
            sys.stderr.write("warning: %s not available (%s)\n" % (modname, e))
            continue
        handlers.update(mod.register_cli(common))
    return ap, handlers


READ_ONLY = {"info", "map", "unused"}


def main(argv=None):
    ap, handlers = build_parser()
    args = ap.parse_args(argv)
    if args.cmd == "new-sprite" and args.sheet and not (args.frame_w and args.frame_h):
        ap.error("--sheet needs --frame-w and --frame-h")
    try:
        p = Project(args.project)
        handlers[args.cmd](p, args)
    except Refused as e:
        print("REFUSED: %s" % e)
        print("Nothing was written.")
        return 1
    if p.writes or p.moves:
        p.commit(args.dry_run)
        if not args.dry_run:
            print("done - run check_project.py, then reload the project in the IDE")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.modules.setdefault("gm", sys.modules["__main__"])   # extension modules share this module's classes
    try:
        sys.exit(main())
    except BrokenPipeError:  # output piped into head etc.; all writes already finished
        sys.exit(0)
