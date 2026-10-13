---
name: game-feel
description: >
  This skill should be used when the user wants a GameMaker game to feel better or more alive: "add juice",
  "game feel", "make hits feel stronger", "screen shake", "hit stop", "freeze frame", "squash and stretch",
  "particles", "white flash when hit", "floating damage numbers", "it feels flat/boring/berbat", or when
  reviewing why a prototype does not feel good to play.
metadata:
  version: "0.1.0"
---

# Game feel in GameMaker

Feel comes from feedback on the player's actions: every action should be answered by the screen, the sound and
the objects involved within a few frames. Work in this order, because each layer is cheaper and more effective
than the next:

1. **Responsiveness** — input acts on the same frame; no long wind-ups; coyote time and input buffering where
   timing matters (see `gml-systems` → Platformer movement). A game that feels "berbat" is often late or vague
   before it is under-decorated.
2. **Readability** — the player can tell what happened: hit flashes, clear knockback direction, distinct sounds
   per event, telegraphs before enemy attacks.
3. **Impact** — hit stop, screen shake, squash and stretch, particles, camera kick.
4. **Polish** — easing on UI, floating text, ambient particles, music changes.

Sound is half of feel. A prototype tested in silence will feel empty no matter how much shake it has — add
placeholder sounds early (even free sound packs or bfxr/sfxr-style generated effects).

## How to apply

- Ask what moment feels weak (catching, hitting, landing, failing) and start there; do not add every effect
  everywhere.
- Keep effect strength in named variables on the controller (`global.shake_scale`, `global.hitstop_scale`) so the
  user can tune them and turn them off (screen shake should be optional for accessibility).
- Prefer one shared helper per effect (`juice_shake(amount)`, `juice_hitstop(frames)`, `juice_burst(x, y, kind)`)
  over copies in each object.
- After adding effects, suggest a 30-second playtest with a specific checklist: does the hit read without
  looking at the HUD? is anything annoying after 2 minutes?

Code for every effect is in `references/effects.md`: screen shake (trauma model), hit stop, squash and stretch,
hit flash, particles, floating text, easing, and a combined "big hit" example.
