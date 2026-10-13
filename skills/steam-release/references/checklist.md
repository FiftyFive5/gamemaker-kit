# Steam pre-release checklist for GameMaker games

Go through it with the user; mark each item done, not applicable, or open.

## Game build
- [ ] Release build uses the intended compiler (YYC if set up, otherwise VM) and has been played start to end.
- [ ] No debug keys, debug overlays, cheat shortcuts or `show_debug_message` spam left in.
- [ ] Game options: correct game name, version number, icon, splash; Windows executable name.
- [ ] Window: starts in a sensible mode, fullscreen toggle works (`window_set_fullscreen`), scales cleanly on
      1280×800 (Steam Deck), 1920×1080 and 2560×1440.
- [ ] Settings menu: volume (music/sfx), fullscreen, screen shake on/off, rebinding if keyboard-heavy.
- [ ] Saves and settings go to the sandboxed save area (default for file functions) and survive an update.
- [ ] Pausing works and the game pauses when a controller disconnects or the window loses focus (if desired).
- [ ] Alt-tab, minimise and resume do not break surfaces (recreate on `!surface_exists`).

## Steam integration
- [ ] Steamworks extension configured; `steam_update()` every step; `steam_shutdown()` in Game End.
- [ ] Achievements defined on the partner site, API names match the code, tested with a test account.
- [ ] Game runs without Steam during development (calls guarded), and relaunches through Steam when started
      directly in release.
- [ ] Builds uploaded with SteamPipe to the default branch; launch options set for each OS; depots configured.
- [ ] Optional: Steam Cloud for saves (configure in partner site; mind conflicts with local saves).

## Steam Deck and controllers
- [ ] Full gamepad support: menus navigable without mouse, on-screen prompts show gamepad buttons when a pad is
      used.
- [ ] Text readable at 1280×800 — test on a Steam Deck or in a window of that size.
- [ ] No launcher or text entry required, or the Steam on-screen keyboard is used.

## Store page (must be "coming soon" ≥ 2 weeks before release)
- [ ] Capsule images in all required sizes, screenshots (at least 5 good ones), trailer (first seconds show
      gameplay), short description that says what the player does.
- [ ] Tags reflect the actual game (e.g. co-op, local co-op, pixel graphics, party, chaotic).
- [ ] Supported languages, controller support flags, system requirements.
- [ ] Mature content survey answered honestly.

## Business
- [ ] Steam Direct fee paid ≥ 30 days before release (first titles); tax and bank info verified.
- [ ] Price chosen and regional pricing reviewed; launch discount decided.
- [ ] Release date shown as a date or "coming soon"; wishlist calls-to-action in trailer and social posts.

## Launch week
- [ ] Press Release in Steamworks (it does not release on its own).
- [ ] Watch discussions and crash reports; have a hotfix build process ready (rebuild → upload → set live).
