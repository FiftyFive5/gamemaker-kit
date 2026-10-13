---
name: steam-release
description: >
  This skill should be used when the user prepares a GameMaker game for Steam: "put my game on Steam",
  "Steamworks setup", "Steam achievements", "upload a build to Steam", "Steam Direct fee", "store page",
  "coming soon page", "release checklist", "Steam Deck support", or asks how long until a GameMaker game can
  be released on Steam.
metadata:
  version: "0.1.0"
---

# Releasing a GameMaker game on Steam

Steam rules, fees and SDK versions change. The facts below were checked against Valve's and GameMaker's
documentation in October 2026; before giving a date or amount as definitive, re-check the linked pages with web
search when it is available, and say when information may be outdated.

## Timeline and costs (Valve)

- **Steam Direct fee:** US$100 per game, non-refundable, recouped once the game earns US$1,000 adjusted gross
  revenue. Paperwork: identity verification, bank details (holder name must match ID), tax forms.
- **Waiting period:** for a developer's first titles, at least 30 days between paying the fee and releasing.
- **Coming soon:** the store page must be public as "coming soon" for at least 2 weeks before release.
- **Reviews:** store page and build are each reviewed by Valve (typically 1–5 business days); submit the store
  page at least a week before you need it live. The build can only be submitted after the store page.
- **Release:** nothing releases automatically — the developer presses Release in Steamworks.

Plan backwards from the target date: fee + paperwork ≥ 30 days before release; store page live ≥ 2 weeks before;
build reviewed before release. Wishlists accumulate while the page is "coming soon", so earlier is better.

Sources: partner.steamgames.com/steamdirect and partner.steamgames.com/doc/store/releasing.

## GameMaker side

1. Install the **official Steamworks extension** (GameMaker Marketplace, or `.yymps` from the
   YoYoGames/GMEXT-Steamworks GitHub releases) and import it into the project.
2. Download the Steamworks SDK version that the extension's guide names for the user's GameMaker version, extract
   it to a short path (e.g. `C:\SteamworksSDK`), and set **Steam SDK** path and **Application ID** in the
   extension's options (double-click the extension in the Asset Browser). Keep the Debug option on Auto.
3. Call `steam_update()` every step from a persistent controller object (required). The extension calls
   `steam_init` itself at game start. Call `steam_shutdown()` in that controller's Game End event, but not when
   the game is restarting via `game_restart()` (set a flag before restarting and skip shutdown when it is set).
4. Steam client must be running and logged in to test. Exports: Windows/Linux as compressed .zip, macOS as
   .app.zip (disable "Build for Mac App Store"; not .dmg). Do not use Steam's DRM wrapper with GameMaker.
5. Upload builds with the SDK's upload tools (SteamPipe); a code change needs a new upload to appear in the
   Steam-launched copy.

## Achievements and stats

- Define achievements and stats in the Steamworks partner site first; code uses their **API names**.
- Wait until `steam_stats_ready()` is true before reading or writing.
- `steam_set_achievement("ACH_FIRST_CATCH")`, `steam_get_achievement(name)`, `steam_clear_achievement(name)`
  (testing only).
- Stats: `steam_set_stat_int(name, value)`, `steam_get_stat_int(name)` (and `_float` variants).
  `steam_indicate_achievement_progress(name, cur, max)` only shows a popup — store the stat too.
- `steam_reset_all_stats_achievements()` is for development only; never ship a code path that calls it.
- Wrap all Steam calls in a small script (`steam_try_achievement(name)`) that checks the extension is
  initialised and stats are ready, so the game still runs outside Steam during development.

## Pre-release checklist

Read `references/checklist.md` and walk through it with the user; it covers build settings, Steam Deck and
controller support, save locations, store page assets and the launch week.
