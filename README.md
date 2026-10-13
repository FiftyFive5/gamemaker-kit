# gamemaker-kit

A Claude plugin for making games in GameMaker.

AI agents write GML well enough, but they break GameMaker projects in a predictable way: they write `.yy` files
from memory. The `.yy` format is undocumented and changes between IDE releases, so a template that worked for one
version produces "project is later than this release", silently ignored events, or a project that will not open.

gamemaker-kit is built on one rule — **the project is the template**. Every new object, event, script or sprite
is cloned from an asset of the same type in your own project, and the scaffolding script refuses to write
anything it cannot reproduce in your project's exact file layout. A checker then runs automatically after every
edit.

## Install

In Claude Code:

```
/plugin marketplace add FiftyFive5/gamemaker-kit
/plugin install gamemaker-kit@gamemaker-kit
```

or in one step (Claude Code 2.1.275+):

```
/plugin install gamemaker-kit --marketplace FiftyFive5/gamemaker-kit
```

## What's inside

### Skills

| Skill | Use it for |
|---|---|
| `gamemaker-assets` | Creating and editing objects, events, scripts, sprites and `.yyp` registrations safely |
| `gml-code` | Writing and debugging GML: `with`/`other`, Create timing, event order, Draw vs Draw GUI, reading error messages |
| `gml-systems` | State machines, top-down and platformer movement, camera, save/load, audio, pause, room transitions |
| `game-feel` | Screen shake, hit stop, squash and stretch, hit flash, particles, floating text, easing |
| `local-coop-input` | Action-based input layer, shared keyboard, gamepad hot-plugging, rebinding, shared camera, split screen |
| `gm-performance` | Debugger and profiler, the usual causes of lag and leaks, texture groups, YYC |
| `steam-release` | Steamworks extension setup, achievements, Valve's timeline and fees, a full pre-release checklist |

### Scripts (Python 3.8+, standard library; sprites need Pillow)

```bash
S=skills/gamemaker-assets/scripts
python3 $S/gm.py info        MyGame/
python3 $S/gm.py new-object  MyGame/ obj_enemy --events Create,Step,Draw,Collision:obj_wall --sprite spr_enemy
python3 $S/gm.py add-event   MyGame/ obj_enemy Alarm0 DrawGUI KeyPress:space
python3 $S/gm.py new-script  MyGame/ scr_helpers
python3 $S/gm.py new-sprite  MyGame/ spr_enemy_walk --sheet walk.png --frame-w 32 --frame-h 32 --origin bottom-centre
python3 $S/check_project.py  MyGame/
```

`gm.py` writes all files first and registers the asset in the `.yyp` last, so an interrupted run never leaves a
registered asset with missing files. Add `--dry-run` to preview.

`check_project.py` reports unparseable files, missing or mismatched files, unknown parent folders, events without
code files, unregistered asset folders, and assets whose format differs from the rest of their type.

### Hook

After Claude writes a `.yy`, `.yyp` or `.gml` file inside a GameMaker project, the checker runs automatically and
reports errors back to Claude. It is silent when the project is clean and ignores files outside GameMaker
projects. It needs `python3` on the PATH (on Windows, install Python from python.org and tick "Add to PATH").
Edits made through a remote shell instead of Claude's file tools do not trigger it; the skills tell Claude to run
the checker itself in that case.

### Agent

`gml-reviewer` reads changed GML with fresh eyes against twelve classic GameMaker traps and the project's own
conventions, and reports *Will break / Likely bug / Style* findings. It never edits files.

## Tips

- Close the project in the GameMaker IDE before letting Claude edit files, or choose **Reload** when the IDE
  notices the change. Saving from the IDE overwrites the changes on disk.
- If your project has no asset of the kind you need yet, create one empty one in the IDE first. The scripts ask
  for this rather than guess the format.
- Rooms, tilesets, fonts and sounds are best edited in the IDE.

## Compatibility

Targets GameMaker 2.3 and later (the JSON-based project format), including the 2024+ releases. Because the format
is read from your own project, it does not depend on a specific IDE version. GameMaker Studio 1.x and 2.2
projects are not supported. Steam facts in `steam-release` were checked in October 2026; Valve's rules change, so
the skill re-checks them when web search is available.

## License

MIT
