#!/usr/bin/env python3
"""Check a GameMaker project folder for the mistakes hand edits usually make.

Usage: check_project.py <project folder or .yyp file>

Reads .yyp/.yy files the way GameMaker writes them (trailing commas allowed),
then reports errors and warnings. Exit code: 0 = no errors, 1 = errors found,
2 = could not run. Standard library only.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

EVENT_PREFIX = {
    0: "Create", 1: "Destroy", 2: "Alarm", 3: "Step", 4: "Collision",
    5: "Keyboard", 6: "Mouse", 7: "Other", 8: "Draw", 9: "KeyPress",
    10: "KeyRelease", 11: "Trigger", 12: "CleanUp", 13: "Gesture", 14: "PreCreate",
}
EVENT_FILE_RE = re.compile(r"^(%s)_(.+)\.gml$" % "|".join(EVENT_PREFIX.values()))


def strip_trailing_commas(text):
    """Remove commas that directly precede } or ], ignoring commas inside strings."""
    out = []
    i, n = 0, len(text)
    in_str = False
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
            if j < n and text[j] in "}]":
                i += 1
                continue
            out.append(c)
        else:
            out.append(c)
        i += 1
    return "".join(out)


def load_yy(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        text = f.read()
    return json.loads(strip_trailing_commas(text))


def ref_name(ref):
    if isinstance(ref, dict):
        return ref.get("name")
    return None


def ref_path(ref):
    if isinstance(ref, dict):
        return ref.get("path")
    return None


def type_signature(data):
    """Keys that identify the format version: $-tags with their values, plus resourceVersion."""
    sig = tuple(sorted((k, str(v)) for k, v in data.items() if k.startswith("$")))
    return sig + (("resourceVersion", str(data.get("resourceVersion"))),)


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def find_yyp(arg):
    if os.path.isfile(arg) and arg.endswith(".yyp"):
        return arg
    if os.path.isdir(arg):
        found = [f for f in os.listdir(arg) if f.endswith(".yyp")]
        if len(found) == 1:
            return os.path.join(arg, found[0])
        if len(found) > 1:
            print("More than one .yyp in %s: %s" % (arg, ", ".join(found)))
            sys.exit(2)
    print("No .yyp found at %s" % arg)
    sys.exit(2)


def check_object(root, name, data, rep):
    obj_dir = os.path.join(root, "objects", name)
    expected = set()
    for ev in data.get("eventList") or []:
        et, en = ev.get("eventType"), ev.get("eventNum")
        prefix = EVENT_PREFIX.get(et)
        if prefix is None:
            rep.warn("%s: unknown eventType %r in eventList" % (name, et))
            continue
        if et == 4:
            other = ref_name(ev.get("collisionObjectId"))
            candidates = ["Collision_%s.gml" % other] if other else []
            if not any(os.path.isfile(os.path.join(obj_dir, c)) for c in candidates):
                existing = [f for f in os.listdir(obj_dir) if f.startswith("Collision_")] if os.path.isdir(obj_dir) else []
                if existing:
                    expected.update(existing)
                    rep.warn("%s: collision event with %s, expected Collision_%s.gml; found %s" % (name, other, other, ", ".join(existing)))
                else:
                    rep.error("%s: collision event with %s has no Collision_*.gml file" % (name, other))
            else:
                expected.update(candidates)
            continue
        fname = "%s_%s.gml" % (prefix, en)
        expected.add(fname)
        if not os.path.isfile(os.path.join(obj_dir, fname)):
            rep.error("%s: event %s (type %s, num %s) is listed but %s is missing" % (name, prefix, et, en, fname))
    if os.path.isdir(obj_dir):
        for f in sorted(os.listdir(obj_dir)):
            if EVENT_FILE_RE.match(f) and f not in expected:
                rep.warn("%s: %s exists but no event in eventList uses it (the IDE will ignore it)" % (name, f))


def check(yyp_path):
    rep = Report()
    root = os.path.dirname(os.path.abspath(yyp_path))
    try:
        project = load_yy(yyp_path)
    except Exception as e:  # noqa: BLE001
        rep.error("%s does not parse: %s" % (os.path.basename(yyp_path), e))
        return rep, None

    meta = project.get("MetaData") or {}
    version = meta.get("IDEVersion")

    folders = set()
    for fo in project.get("Folders") or []:
        p = fo.get("folderPath") or fo.get("path")
        if p:
            folders.add(p)

    registered_paths = set()
    names = Counter()
    sigs = defaultdict(lambda: defaultdict(list))

    for entry in project.get("resources") or []:
        ref = entry.get("id", entry)
        name, path = ref_name(ref), ref_path(ref)
        if not name or not path:
            rep.error("resources entry without name/path: %s" % json.dumps(entry)[:120])
            continue
        names[name] += 1
        registered_paths.add(os.path.normpath(path))
        full = os.path.join(root, path)
        if not os.path.isfile(full):
            rep.error("%s is registered but %s does not exist" % (name, path))
            continue
        try:
            data = load_yy(full)
        except Exception as e:  # noqa: BLE001
            rep.error("%s does not parse: %s" % (path, e))
            continue
        if data.get("name") != name:
            rep.error("%s: .yy says name %r but the project registers it as %r" % (path, data.get("name"), name))
        if "%Name" in data and data["%Name"] != name:
            rep.error("%s: %%Name is %r, expected %r" % (path, data["%Name"], name))
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem != name or os.path.basename(os.path.dirname(path)) != name:
            rep.error("%s: folder and file name must both be %r" % (path, name))
        parent_path = ref_path(data.get("parent"))
        if parent_path and parent_path.startswith("folders/") and folders and parent_path not in folders:
            rep.error("%s: parent folder %s is not in the project's Folders list" % (name, parent_path))
        rtype = data.get("resourceType") or path.split("/")[0]
        sigs[rtype][type_signature(data)].append(name)
        if rtype == "GMObject" or path.startswith("objects/"):
            check_object(root, name, data, rep)
            for key in ("spriteId", "parentObjectId", "spriteMaskId"):
                rp = ref_path(data.get(key))
                if rp and not os.path.isfile(os.path.join(root, rp)):
                    rep.error("%s: %s points to %s, which does not exist" % (name, key, rp))
        if rtype == "GMScript" or path.startswith("scripts/"):
            gml = os.path.join(root, os.path.dirname(path), name + ".gml")
            if not os.path.isfile(gml):
                rep.error("%s: script code file %s.gml is missing" % (name, name))

    for name, count in names.items():
        if count > 1:
            rep.error("%s is registered %d times" % (name, count))

    for rtype, groups in sigs.items():
        if len(groups) > 1:
            ranked = sorted(groups.items(), key=lambda kv: -len(kv[1]))
            if len(ranked[0][1]) == len(ranked[1][1]):
                desc = "; ".join("%s: %s" % (dict(sig), ", ".join(sorted(m)[:5])) for sig, m in ranked)
                rep.warn("%s assets use %d different formats (%s) - one was probably copied from another IDE version" % (
                    rtype, len(ranked), desc))
                continue
            majority = ranked[0][0]
            for sig, members in ranked[1:]:
                rep.warn("%s format differs from the other %d %s assets (%s vs %s): %s" % (
                    ", ".join(sorted(members)[:5]), len(ranked[0][1]), rtype,
                    dict(sig), dict(majority), "copied from another IDE version?"))

    asset_dirs = ("objects", "sprites", "scripts", "rooms", "sounds", "fonts", "paths",
                  "tilesets", "sequences", "shaders", "timelines", "animcurves", "notes", "extensions")
    for d in asset_dirs:
        base = os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        for sub in sorted(os.listdir(base)):
            yy = os.path.normpath(os.path.join(d, sub, sub + ".yy"))
            if os.path.isfile(os.path.join(root, yy)) and yy not in registered_paths:
                rep.warn("%s exists on disk but is not registered in the .yyp (the IDE will not show it)" % yy)

    return rep, version


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    yyp = find_yyp(sys.argv[1])
    rep, version = check(yyp)
    print("Project: %s%s" % (os.path.basename(yyp), " (IDE %s)" % version if version else ""))
    for e in rep.errors:
        print("ERROR   " + e)
    for w in rep.warnings:
        print("WARNING " + w)
    print("%d error(s), %d warning(s)" % (len(rep.errors), len(rep.warnings)))
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
