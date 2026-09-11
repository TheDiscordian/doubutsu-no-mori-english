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

Further scenic footage and the finished edit are in progress. Do not claim
that a recorded scenario's successful exit alone proves usable footage.

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

## Remaining

- Choose inspected current-build shots, excluding the rejected name take.
- Build the typography, motion, cut sequence, soundtrack mix, and final MP4.
- Check representative frames, all transitions, duration, audio levels, and
  absence of emulator borders, rejected name, or unsupported release claims.
- Commit/push production sources and hand over the local video without
  automatic physical audio playback or public publication.
