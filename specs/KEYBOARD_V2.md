# V2 N64-inspired keyboard

## Status and prerequisite

Deferred until V1 is fully complete. This is a requested future design, not
part of the current V1 correction batch. A V1 candidate, implemented fixes,
or passing focused tests alone do not satisfy this prerequisite. Keep the
remaining V1 implementation, review, and acceptance work ahead of V2.

## Requested presentation

- Keep a layout similar to the English GameCube keyboard.
- Use a greyer background inspired by the Nintendo 64 controller.
- Use button images matching the N64 controller and the actual input bindings.
- Include a control-stick image on the left, as in the GC layout and original
  N64 keyboard. Prefer the existing native artwork where suitable.

## Retained behaviour

Preserve V1's accepted keyboard sounds, corrected corner/label positioning,
consolidated symbol page, proportional editor, N64 input controls, and save
compatibility. The visual redesign must not silently remap controls or imply
GameCube-only buttons. Review the native stick/button assets when V2 starts;
no new artwork extraction, recolouring, or implementation is required now.

Current V1 keyboard work remains limited to its reported defects. Do not use
this future design as a reason to replace the current correction with a larger
controller redesign or delay the next combined V1 playtest build.
