# Private translation trailer

## Scope

Finish the current V2 keyboard corrections first, then create a finished,
catchy trailer using real emulator footage of this translation. Keep the video
private; making a trailer is not approval to publish the project or ROM.

Aim for a concise landscape trailer with a strong opening, lively musical
timing, readable feature captions, clean gameplay, and a memorable closing
title. Preserve the game's 4:3 proportions within the composed video. Crop
emulator borders, menus, debug messages, and desktop details out of all footage.
Do not invent gameplay or show an emulated feature as proof of hardware testing.

Capture in an isolated background emulator using copied test data. Preserve
the user's cartridge saves and desktop session. Encode the soundtrack to a
file without playing audio through speakers or headphones. Use the actual Animal
Crossing opening music to carry the journey through the translated game. Record
the source and keep copyrighted recordings in ignored local outputs only.

The creative direction is entering Animal Crossing, not a product presentation.
Open with the game's opening and English title, then follow a coherent sequence
through meeting Rover, entering a name on the N64-inspired English keyboard,
reading English conversations, and exploring the town and translated interfaces.
Match each feature to footage that visibly demonstrates it. Keep added text
short, natural, and secondary to the game. No numbered feature cards or generic
marketing claims. The title screen is a central highlight, not a brief footnote.

Show the keyboard once, during name entry. Use the remaining montage to reveal
the breadth of the translation: building signs, interiors, map/menu screens,
and the notice board. Preserve the opening and musical journey, but do not
spend multiple feature shots demonstrating the same keyboard.

Use installed tools and existing Docker images before obtaining more tooling.
Keep scripts, edit decisions, captions, music source, and build instructions in
the private repository. Generated footage, extracted art, audio, and final
video remain ignored. Verify the finished render with metadata, representative
frames, transition checks, and audio measurements; do not require the user to
participate in production or claim an unheard soundtrack was auditioned.

## Deliverables

- Finished local MP4 with clean gameplay and a soundtrack.
- Reproducible edit/music sources and footage provenance.
- A work record identifying the exact game build, footage sessions, output
  hashes, checks, and any remaining review limits.

## Production

`tools/emulator_smoke.py --record-video` captures a real-time, isolated display.
Adding `--record-game-audio` records only the monitor of a verified private null
sink. The ordinary capture remains internally muted, and no capture changes
the user's default output or records a microphone. Saved files are copied into
fresh capture directories. The optional `tools/trailer_daytime.py` fixture stages
only a disposable emulator RTC beside an unchanged copy of the supplied town.

`tools/trailer_edit.py --output build/<fresh-directory>` renders the active
66.5-second edit. Its explicit footage allowlist, source hashes, and exact frame
counts are stored with the output. Music comes from the current ROM's native
opening recording and receives only level mastering and a closing fade.
The source build is the current V2 correction cartridge, not an old release.

`tools/trailer_review.py build/<directory>` decodes the complete result and
produces one-second timeline sheets, transition strips, full-size inspection
frames, and audio measurements without physical playback. Inspect those frames
before marking the visual review complete. Focused production checks live in
`tests/test_trailer.py`; they do not launch an emulator or replay old game tests.
