"""Safe asset rename for gm.py.

  rename <project> <old_name> <new_name>

Renames the asset folder and its files, every reference in .yy/.yyp files (parents, sprites, collision
events, room instances, the resources list) and every whole-word use in GML. Writes happen only after the
folder rename succeeds, so a failure leaves the project untouched.
"""
import json
import os
import re

import gm
from gm import Refused

JSON_STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _rename_json_text(text, old, new):
    """Rewrite JSON string values equal to the old name or containing it as a path segment."""
    count = [0]

    def fix(m):
        raw = m.group(1)
        try:
            s = json.loads('"%s"' % raw)
        except ValueError:
            return m.group(0)
        if s == old:
            out = new
        elif "/" in s:
            parts = s.split("/")
            changed = [new if p_ == old else (new + p_[len(old):] if p_.startswith(old + ".") else p_)
                       for p_ in parts]
            out = "/".join(changed)
        else:
            return m.group(0)
        if out == s:
            return m.group(0)
        count[0] += 1
        return json.dumps(out, ensure_ascii=False)
    return JSON_STRING_RE.sub(fix, text), count[0]


def _read(path):
    with open(path, "rb") as f:
        raw = f.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig"), bom


def cmd_rename(p, args):
    old, new = args.old, args.new
    if old not in p.names:
        raise Refused("%s is not an asset in this project" % old)
    p.check_new_name(new)
    old_path = p.path_of(old)
    kind_dir = old_path.split("/")[0]
    old_dir = p.abs("%s/%s" % (kind_dir, old))
    new_dir = p.abs("%s/%s" % (kind_dir, new))
    if os.path.basename(os.path.dirname(p.abs(old_path))) != old:
        raise Refused("%s is not stored in a folder named after it; rename it in the IDE" % old)
    if os.path.exists(new_dir):
        raise Refused("a folder %s already exists" % os.path.relpath(new_dir, p.root))

    word = re.compile(r"\b%s\b" % re.escape(old))
    changes = []         # (path_before_move, new_text, bom)
    renames_outside = []  # (src, dst) for Collision_<old>.gml in other objects
    yy_refs = gml_refs = 0
    for root, dirs, files in os.walk(p.root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "_gmkit_removed"]
        for fn in files:
            path = os.path.join(root, fn)
            if fn.endswith((".yy", ".yyp")):
                text, bom = _read(path)
                fixed, n = _rename_json_text(text, old, new)
                if n:
                    changes.append((path, fixed, bom))
                    yy_refs += n
            elif fn.endswith(".gml"):
                text, bom = _read(path)
                fixed, n = word.subn(new, text)
                if n:
                    changes.append((path, fixed, bom))
                    gml_refs += n
                if fn == "Collision_%s.gml" % old and os.path.dirname(path) != old_dir:
                    renames_outside.append((path, os.path.join(root, "Collision_%s.gml" % new)))

    # verify every changed .yy still parses before touching the disk
    for path, text, _ in changes:
        if path.endswith((".yy", ".yyp")):
            try:
                json.loads(gm.strip_trailing_commas(text))
            except ValueError as e:
                raise Refused("renaming would break %s (%s)" % (os.path.relpath(path, p.root), e))

    inner = [fn for fn in os.listdir(old_dir) if os.path.splitext(fn)[0] == old]
    print("rename %s -> %s: folder, %d file(s) named after it, %d .yy reference(s), %d GML use(s), "
          "%d collision file(s) in other objects" % (old, new, len(inner), yy_refs, gml_refs,
                                                    len(renames_outside)))
    if gml_refs:
        print("note: GML is renamed by whole word, including inside strings and comments")
    if args.dry_run:
        for path, _, _ in changes:
            print("would update %s" % os.path.relpath(path, p.root))
        return

    try:
        os.rename(old_dir, new_dir)
    except OSError as e:
        raise Refused("could not rename the folder (%s). Nothing was changed. Rename %s in the IDE instead."
                      % (e, old))
    for fn in inner:
        os.rename(os.path.join(new_dir, fn), os.path.join(new_dir, new + fn[len(old):]))
    for path, text, bom in changes:
        if path.startswith(old_dir + os.sep):
            rest = os.path.relpath(path, old_dir)
            if os.path.splitext(rest)[0] == old:
                rest = new + rest[len(old):]
            path = os.path.join(new_dir, rest)
        with open(path, "wb") as f:
            f.write((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
        print("update %s" % os.path.relpath(path, p.root))
    for src, dst in renames_outside:
        os.rename(src, dst)
        print("rename %s" % os.path.relpath(dst, p.root))
    print("done - run check_project.py, then reload the project in the IDE")


def register_cli(common):
    sp = common("rename", help="rename an asset everywhere")
    sp.add_argument("old")
    sp.add_argument("new")
    return {"rename": cmd_rename}
