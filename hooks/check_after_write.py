#!/usr/bin/env python3
"""PostToolUse hook: after Claude writes a .yy, .yyp or .gml file inside a GameMaker project,
run the project checker and report errors back to Claude. Silent when the project is clean
or when the file is not part of a GameMaker project."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "gamemaker-assets", "scripts"))


def project_root(path):
    d = os.path.dirname(os.path.abspath(path))
    for _ in range(8):
        try:
            if any(f.endswith(".yyp") for f in os.listdir(d)):
                return d
        except OSError:
            return None
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not path.endswith((".yy", ".yyp", ".gml")):
        return 0
    root = project_root(path)
    if not root:
        return 0
    try:
        import check_project
        yyp = check_project.find_yyp(root)
        rep, _ = check_project.check(yyp)
    except SystemExit:
        return 0
    except Exception as e:  # never break the session because of the checker
        sys.stderr.write("gamemaker-kit checker failed: %s\n" % e)
        return 0
    if not rep.errors:
        return 0
    lines = ["GameMaker project check found %d error(s) after this edit:" % len(rep.errors)]
    lines += ["- " + e for e in rep.errors[:15]]
    if len(rep.errors) > 15:
        lines.append("- … %d more" % (len(rep.errors) - 15))
    lines.append("If this edit is one step of several (e.g. the .gml files come next), continue and the "
                 "check runs again; otherwise fix these before telling the user the project is ready.")
    print(json.dumps({"decision": "block", "reason": "\n".join(lines)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
