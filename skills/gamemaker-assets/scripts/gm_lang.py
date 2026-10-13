"""Localization helpers for gm.py.

  extract-strings <project> [--csv localization.csv] [--langs tr,de] [--apply]
      Finds player-facing text (string literals passed to draw_text*, show_message, show_question,
      juice_text) and writes/merges them into a CSV (key, en, tr, ...). With --apply the literals in
      code are replaced by tr("key") and the scr_lang script is generated.
  build-lang <project> [--csv localization.csv]
      Regenerates scr_lang from the CSV after translations were filled in.

In game: lang_set("tr"); draw_text(x, y, tr("paused"));  Missing translations fall back to the source text.
"""
import csv
import io
import os
import re

import gm
from gm import Refused

CALL_RE = re.compile(r"\b(draw_text\w*|show_message|show_question|juice_text)\s*\(")
COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
LITERAL_RE = re.compile(r'(?<![$@\w])"((?:[^"\\\n]|\\.)*)"')
SCRIPT = "scr_lang"


def _mask_comments(text):
    return COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def _call_spans(code):
    """(start, end) of the argument list of every matching call, respecting strings and nesting."""
    for m in CALL_RE.finditer(code):
        i, depth, in_str = m.end(), 1, False
        while i < len(code) and depth:
            c = code[i]
            if in_str:
                if c == "\\":
                    i += 1
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            i += 1
        yield m.end(), i - 1


def find_texts(text):
    """[(start, end, literal_content)] for player-facing literals in one GML file."""
    code = _mask_comments(text)
    found = []
    for a, b in _call_spans(code):
        for lm in LITERAL_RE.finditer(code, a, b):
            content = lm.group(1)
            if re.search(r"[A-Za-z]{2}", content):
                found.append((lm.start(), lm.end(), content))
    return found


def _slug(text, taken):
    plain = re.sub(r"\\.", " ", text)
    words = re.findall(r"[A-Za-z0-9]+", plain.lower())[:4] or ["text"]
    base = "_".join(words)
    if base[0].isdigit():
        base = "t_" + base
    key, n = base, 2
    while key in taken:
        key, n = "%s_%d" % (base, n), n + 1
    return key


def _csv_path(p, args):
    return args.csv if args.csv and os.path.isabs(args.csv) else os.path.join(p.root, args.csv or "localization.csv")


def read_csv(path):
    if not os.path.isfile(path):
        return [], {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows or rows[0][0] != "key" or len(rows[0]) < 2:
        raise Refused("%s does not start with a key,<language>,... header" % path)
    langs = rows[0][1:]
    table = {}
    for r in rows[1:]:
        if r and r[0]:
            table[r[0]] = {lang: (r[i + 1] if i + 1 < len(r) else "") for i, lang in enumerate(langs)}
    return langs, table


def write_csv(p, path, langs, table):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["key"] + langs)
    for key in sorted(table):
        w.writerow([key] + [table[key].get(l, "") for l in langs])
    p.queue(path, buf.getvalue(), bom=True)


def _gml_string(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            out.append(s[i:i + 2])
            i += 2
            continue
        out.append('\\"' if c == '"' else ("\\n" if c == "\n" else c))
        i += 1
    return '"%s"' % "".join(out)


def lang_script(langs, table):
    src = langs[0]
    lines = ["/// gamemaker-kit: generated from localization.csv by `gm.py build-lang`. Do not edit by hand —",
             "/// edit the CSV and run build-lang again.", "",
             'global.lang = "%s";' % src, "global.lang_table = {};"]
    for lang in langs:
        lines.append('global.lang_table[$ "%s"] = {};' % lang)
        for key in sorted(table):
            val = table[key].get(lang, "")
            if val:
                lines.append('global.lang_table[$ "%s"][$ "%s"] = %s;' % (lang, key, _gml_string(val)))
    lines += ["",
              "/// Text for a key in the current language, falling back to %s, then to the key itself." % src,
              "function tr(_key) {",
              "    var t = global.lang_table[$ global.lang];",
              "    var s = is_undefined(t) ? undefined : t[$ _key];",
              '    if (is_undefined(s)) s = global.lang_table[$ "%s"][$ _key];' % src,
              "    return is_undefined(s) ? _key : s;",
              "}", "",
              "/// Switch language; returns false if the language is not in the table.",
              "function lang_set(_code) {",
              "    if (is_undefined(global.lang_table[$ _code])) return false;",
              "    global.lang = _code;",
              "    return true;",
              "}", "",
              "function lang_list() {",
              "    return variable_struct_get_names(global.lang_table);",
              "}", ""]
    return "\n".join(lines)


def _write_lang_script(p, langs, table):
    code = lang_script(langs, table)
    if SCRIPT in p.names:
        gml = os.path.join(os.path.dirname(p.abs(p.path_of(SCRIPT))), SCRIPT + ".gml")
        p.queue(gml, code)
    else:
        gm.create_script(p, SCRIPT, code)


def cmd_extract(p, args):
    path = _csv_path(p, args)
    langs, table = read_csv(path)
    if not langs:
        langs = [args.source]
    for l in [x.strip() for x in (args.langs or "").split(",") if x.strip()]:
        if l not in langs:
            langs.append(l)
    src = langs[0]
    by_text = {v.get(src, ""): k for k, v in table.items()}
    total, new_keys, files_changed = 0, 0, 0
    for root, dirs, files in os.walk(p.root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "_gmkit_removed"]
        for fn in files:
            if not fn.endswith(".gml") or fn == SCRIPT + ".gml":
                continue
            full = os.path.join(root, fn)
            with open(full, "r", encoding="utf-8-sig") as f:
                text = f.read()
            hits = find_texts(text)
            if not hits:
                continue
            out, last = [], 0
            for a, b, content in hits:
                total += 1
                key = by_text.get(content)
                if not key:
                    key = _slug(content, table)
                    table[key] = {l: "" for l in langs}
                    table[key][src] = content
                    by_text[content] = key
                    new_keys += 1
                out.append(text[last:a])
                out.append('tr("%s")' % key)
                last = b
            out.append(text[last:])
            if args.apply:
                p.queue(full, "".join(out))
                files_changed += 1
    print("found %d text(s), %d new key(s), %d language column(s): %s" % (total, new_keys, len(langs),
                                                                         ", ".join(langs)))
    write_csv(p, path, langs, table)
    if args.apply:
        _write_lang_script(p, langs, table)
        print("replaced text with tr(\"key\") in %d file(s)" % files_changed)
    else:
        print("review the CSV, then run again with --apply to replace the text in code with tr(\"key\")")


def cmd_build(p, args):
    langs, table = read_csv(_csv_path(p, args))
    if not langs:
        raise Refused("no localization CSV yet; run extract-strings first")
    _write_lang_script(p, langs, table)
    missing = {l: sum(1 for v in table.values() if not v.get(l)) for l in langs[1:]}
    print("scr_lang rebuilt: %d keys; missing translations: %s" % (
        len(table), ", ".join("%s %d" % kv for kv in missing.items()) or "none"))


def register_cli(common):
    sp = common("extract-strings", help="collect player-facing text into a CSV")
    sp.add_argument("--csv")
    sp.add_argument("--langs")
    sp.add_argument("--source", default="en")
    sp.add_argument("--apply", action="store_true")
    sp = common("build-lang", help="regenerate scr_lang from the CSV")
    sp.add_argument("--csv")
    return {"extract-strings": cmd_extract, "build-lang": cmd_build}
