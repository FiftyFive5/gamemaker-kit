# Object events: file names and numbers

Each entry in an object's `eventList` has an `eventType` and an `eventNum`. The event's code is in a `.gml` file
next to the object's `.yy`, named `<Prefix>_<eventNum>.gml`. Always copy the shape of an existing `eventList`
entry from the same project — only `eventType`, `eventNum` and (for collisions) `collisionObjectId` change.

These numbers have been stable since GameMaker Studio 2.3. If the project's own files disagree with this table,
the project wins.

| eventType | Event | File prefix | Common eventNum values |
|---|---|---|---|
| 0 | Create | `Create` | 0 |
| 1 | Destroy | `Destroy` | 0 |
| 2 | Alarm | `Alarm` | 0–11 (alarm index) |
| 3 | Step | `Step` | 0 Step, 1 Begin Step, 2 End Step |
| 4 | Collision | `Collision` | 0, with `collisionObjectId` naming the other object |
| 5 | Keyboard (held) | `Keyboard` | key code |
| 6 | Mouse | `Mouse` | mouse event number |
| 7 | Other | `Other` | 2 Game Start, 3 Game End, 4 Room Start, 5 Room End, 7 Animation End, 10–25 User Event 0–15, … |
| 8 | Draw | `Draw` | 0 Draw, 64 Draw GUI, 72 Draw Begin, 73 Draw End, 74 Draw GUI Begin, 75 Draw GUI End, 76 Pre-Draw, 77 Post-Draw, 65 Window Resize |
| 9 | Key Press | `KeyPress` | key code |
| 10 | Key Release | `KeyRelease` | key code |
| 12 | Clean Up | `CleanUp` | 0 |
| 13 | Gesture | `Gesture` | gesture number |
| 14 | Pre-Create | `PreCreate` | 0 |

Examples: `Step_2.gml` is End Step, `Draw_64.gml` is Draw GUI, `Alarm_3.gml` is Alarm 3, `Other_10.gml` is User
Event 0.

## Collision events

`collisionObjectId` holds a reference (`name` and `path`) to the other object, copied in the same shape the
project uses for other asset references (for example its `parent` or `spriteId` fields). The code file is
normally `Collision_<other object name>.gml`. Before adding the first collision event to a project, look for an
existing `Collision_*.gml` anywhere in the project to confirm the naming used by this IDE version; if there is
none, ask the user to add one collision event in the IDE first and copy that.

## Key codes

Keyboard events use virtual key codes: letters are their uppercase ASCII code (`A` = 65), digits 48–57,
`vk_left` 37, `vk_up` 38, `vk_right` 39, `vk_down` 40, `vk_space` 32, `vk_enter` 13, `vk_escape` 27. Polling
input in a Step event (`keyboard_check`, `keyboard_check_pressed`) is usually simpler than adding one event per
key, and avoids `.yy` edits altogether.
