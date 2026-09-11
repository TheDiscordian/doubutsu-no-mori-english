# Private trailer work record

## Active production

The current game build is `build/v2-keyboard-06`, ROM SHA-256
`259543536db43733d4a73ede05949ba52b1ce4ac3c557fc1c8e97b205856ad12`.
The V2 feedback correction is committed as `4a081a1` and pushed to the private
repository. Trailer production follows the authorised scope in
`specs/TRAILER.md`. No public upload is made or authorised.

The edit follows the actual opening music through the English title, Rover,
name entry, conversations, and town life. The game occupies most of the frame;
added captions are brief and tied to the demonstrated translation work. Footage
and audio are in ignored `build/` paths.

The first assembled cut (`build/trailer-cut-02`) is a rejected rough cut, not
the finished deliverable. Its synthetic instrumental, repeated presentation
cards, and weak relationship between captions and footage do not meet the
user's direction. It is retained as a work artifact only.

The replacement music is recorded from the current cartridge's actual opening
in `build/trailer-opening-01`. Audio is routed to a verified temporary null
sink and captured from that sink's explicit monitor; no hardware playback or
default-device recording occurs. The recording contains the native N64 chime
and title theme, with a measured rhythmic interval of approximately 0.509
seconds. No generated remix or synthetic substitute is planned.

Additional footage uses a disposable copy of the user's saved town with its
own staged daytime cartridge clock. `tools/trailer_daytime.py` preserves the
original save contents and host clock. Normal controller actions supply the
gameplay; no player teleport or progression injection is used.

## Capture

`tools/emulator_smoke.py --record-video` records its isolated 800×640 X display
at 30 fps using `tools/trailer_capture.py`. The muted emulator uses a temporary
private null sink for real-time audio pacing: captured status shows 59–60 VPS,
not the silent test runner's unthrottled speed. Its stream is observed on that
sink, with no physical routing. The module is removed after recording; default
sinks and user audio settings are untouched. No audio is played to hardware.

The final edit must crop emulator menus, status, and borders. Full game crop
is planned as 752×564 at `(8,34)`, preserving 4:3, with a separate closer
keyboard framing only where deliberate. Captured frames must be inspected
before the edit is finalised.

Available takes:

- `build/trailer-title-01/footage.mkv`: 31.1 seconds, native animated English
  title and daytime attract scene. Both inspection frames are clean in-game.
- `build/trailer-town-01`: loading setup and Limberg's welcome. Timing adapted
  from an unthrottled scenario reaches the actual title Start later than planned;
  take labels do not establish that a scene is gameplay. Do not blindly select
  its `town-arrival` or `inventory` markers as town/inventory footage.
- `build/trailer-town-02`: ordinary loaded town at night and actual inventory.
  User-supplied save is only read/copied from `local/rc2-save-report-g3O4lU`;
  its stored original remains intact. Player `Disco`, town `Meow`.
- `build/trailer-keyboard-02`: corrected name-entry and Rover dialogue, with
  player name `Fae` verified as `466165202020` in the native editor snapshot.
- `build/trailer-keyboard-01` is REJECTED: a mistyped player name. The user
  explicitly excludes that name from the trailer. Never select any frame or
  clip from this take. Use an explicit footage allowlist, not directory globs.

The approved game-led edit uses these inspected takes instead of the initial
nighttime exploration:

| Source directory | Selected content |
| --- | --- |
| `build/trailer-opening-01` | Native N64 chime, actual title music, opening train arrival, and English logo |
| `build/trailer-kk-01` | Complete K.K. welcome and “You can do what you like” dialogue, held for reading |
| `build/trailer-keyboard-03` | Verified `Fae` entry, lowercase switching, native controls, and a longer Rover reaction |
| `build/trailer-daytime-02` | Leaving home and opening the English inventory |
| `build/trailer-daytime-03` | Walking into the town square towards the translated notice sign |
| `build/trailer-board-02` | Existing town note followed by the native English board instructions |

The keyboard's final native snapshot is `466165202020`; no rejected-name
footage is an input. Native captures remain 59–60 VPS around the observed
frames, with ordinary small pacing variation. The board and longer dialogue
takes deliberately leave reading time before advancing. The finished edit is
66.5 seconds, using the native theme's opening and final phrase, with no tempo
change. The soundtrack measures approximately −17.95 LUFS / −1.50 dBTP after
mastering. This is a measurement, not a listening-review claim.

`tools/trailer_edit.py` crops clean gameplay into a full-height 4:3 foreground,
with a soft extension of the same shot at the sides. Short, settling feature
labels replace the presentation cards. No added text covers the dialogue.
The keyboard close view includes the entire stick and all keyboard edges.
The final title identifies the unofficial project and Expansion Pak requirement.
The rejected rough composition remains reproducible from commit `823c358`;
its synthetic soundtrack is not used in the active edit.

## Rejected original music experiment

`tools/trailer_music.py` composes `First Day, New Neighbours`: 24 bars at
120 BPM plus a resolving tail, fifty seconds total. Nylon guitar, marimba,
acoustic bass, soft electric piano, celesta, and light percussion provide a
playful instrumental. No existing game melody or commercial recording is used.

`build/trailer-music-01/soundtrack.wav` is stereo 48-kHz / 24-bit PCM, SHA-256
`e8aa5c88e2a0e473c1e0e57743cf9e30f857dc6b8b920e9ccb1601dbe3257214`.
The first mastering report measures −15.49 LUFS and −1.50 dBTP. Listening review
is not claimed: nothing is auditioned through speakers or headphones.

FluidSynth renders directly to a file, using the installed MIT-licensed
FluidR3 GM SoundFont. Its copyright is Frank Wen, and the full notice is
preserved alongside the render. MIDI, composition code, source hashes, and
render/mastering logs support reproduction. No package installation is needed.

## Capture observations

One concurrent train-capture launch (`build/trailer-train-01`) exits in the
host emulator with SIGSEGV before its OpenGL/game-load/debugger messages. It
does not establish a cartridge crash. The retained host coredump and empty
game log distinguish this from an observed running-game defect. A sequential,
muted train capture uses the already recorded opening song rather than starting
another simultaneous audible-to-null-sink emulator. No historical ROM is tested.

## Finished private edit

File: `build/trailer-cut-04/Animal Forest English - Trailer.mp4`.

- SHA-256: `17cf6e6e53656e58e3d0bf376e76be5e94f675698e43a18b4a298de4fda5179c`.
- Size: 63,746,621 bytes; duration 66.5 seconds / 1,995 video frames.
- 1920×1080, 30 fps, H.264 / yuv420p, stereo AAC, MP4 fast-start.
- Final encoded audio: −18.06 LUFS, −1.26 dBTP; no sample/peak clipping is indicated.
- Seven focused trailer checks pass in 0.609 seconds. Four capture-input checks
  pass in 0.002 seconds. Neither suite runs an emulator or historical ROM.
- Complete video/audio decode finishes without errors. All four one-second
  timeline sheets and all ten four-frame transition strips are inspected.
  Full-size final Rover, keyboard, and closing frames, plus source dialogue,
  inventory, and notice-board frames, receive separate visual inspection.
- The English title is central to both opening and closing. Dialogue is held
  long enough to finish its selected passages. The selected keyboard close-up
  includes the stick and all edges, and shows lowercase input rather than the
  mostly empty part of the symbol page. The final uses only the approved `Fae`
  name-entry footage; the town player is `Disco`.
- All temporary recording sinks are removed. The original copied user saves
  retain SHA-256 `d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.

`edit.json`, `music.json`, `video.json`, and `review/checks.json` beside the
output retain the exact inputs, timing, source hashes, audio provenance, and
verification. Local footage and generated audio/video are ignored by Git.
The script and documentation changes are version-tracked in the private repo.
The prior rough cuts are not the handoff.

No physical listening audition or public release is claimed. Human review of
the trailer's creative result remains the next decision. The video is complete
for that review; no user action is required to finish rendering it.
