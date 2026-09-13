# Ordinary Saturday-evening K.K. performance check

## Scope

The user requests an ordinary gameplay test of the V2-08 credits-freeze fix:
load a town after 8 p.m. Saturday, leave home, and walk north to K.K. The
identified overflow belongs to the shared credits drawer, not K.K. Dirge's
audio or request handling. Do not describe it as a Dirge-only correction or
claim that every song has been played.

## Current-cartridge run

The unchanged V2-08 ROM has SHA-256
`08aa1c4418848138803059a68de667f473f9da490d7c0866ee501c58b8d0896b`.
The source town save has SHA-256
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`;
its preserved copy still matches after testing.

`tools/trailer_daytime.py --output build/kk-saturday-seed-01 --clock
2026-09-12T20:15:00` stages a disposable emulator clock and copies that save.
The game visibly confirms Saturday evening after 8 p.m. Neither the host clock
nor the original save is changed. Expansion Pak is enabled. The emulator is
internally muted and paced through its own private null sink, never hardware.

`build/kk-performance-ordinary-01/` records the current-ROM cold boot, player
selection, normal town entry, and walking north from the house to the station.
The first idle action requested 600 seconds, but the existing runner clamps each
wait to 60 seconds. It gracefully saves a checkpoint at the station and exits;
this is a recording setup limit, not a game failure.

`build/kk-performance-ordinary-02/` resumes that identical-ROM checkpoint. Its
waits use bounded 50-second actions. There is no repeated boot or old-build test.
Ordinary controller input is recorded in `ordinary-controls.jsonl`, with
approximate offsets into the unedited `footage.mkv`. Screenshots come from the
isolated X display. No game code, position, event flag, inventory, or credits
timer is injected or modified through the debugger.

The player walks in front of K.K., selects `Play it!`, and selects `Not really.`
when asked for a request. K.K. chooses **K.K. Western**. The complete performance
runs through the credit roll and back to `Hey, thanks for listening.`. From the
opening-credits capture through that return, there are no controller inputs or
debugger checks interrupting the song. K.K. then
offers the K.K. Western aircheck through the normal dialogue.

The source images `performance-start.png`, `performance-middle.png`,
`performance-late.png`, and `performance-reward.png` establish the opening
credits, later animated credits, return to dialogue, and matching song reward.
The user also reports that the result looks much better; this is appearance
feedback, not an inferred exhaustive hardware or all-song test.

## Continuous-frame result

`tools/kk_performance_review.py --run build/kk-performance-ordinary-02 --start
289 --duration 156` analyses 4,680 consecutive recorded frames spanning the
performance transition, credits, and return to dialogue. The crop is the actual
752×564 game picture at `(8,34)`, excluding emulator chrome and its changing
VPS counter. FFmpeg's freeze detector uses noise tolerance 0.001 and a 0.5-second
minimum interval. It reports **zero frozen intervals of 0.5 seconds or longer**.
This is a thresholded video measurement, not proof that every frame renders
at a fixed rate or that no shorter hiccup occurs.

The full recording SHA-256 is
`12fafc302f4918d7fd9e677febc20576dd9fd83333f012cf3e82fc13f0ad4f60`.
`freeze-review.json`, `freeze-review.log`, and `freeze-metadata.txt` retain the
exact measurement. End-of-run fault/module checks pass and the emulator exits
gracefully. Post-performance dialogue and the aircheck offer are inspected;
no additional gameplay or save/restart cycle is claimed.

## Reuse and limits

The ordinary scenarios, bounded controller utility, and recorded-video freeze
review remain in `tests/kk-performance-*.json` and `tools/kk_performance_*.py`.
Use the installed X display belonging to the isolated run; resumed sessions may
receive a different display number. All recordings, copied saves, and screenshots
remain ignored local evidence. The released trailer is untouched.

This is one complete emulator performance of a different automatically selected
song. It supplements the [all-page native buffer test](V2_PERFORMANCE_FIXES.md)
without claiming every song, request variant, or original-hardware configuration
has been tested. No additional ROM or patch changes are needed for this check.
