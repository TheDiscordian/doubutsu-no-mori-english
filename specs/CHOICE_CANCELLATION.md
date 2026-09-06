# GameCube choice cancellation

## Behaviour

GameCube command `62` sets the choice window's existing B-to-last-option flag
and its no-close-sound flag. The N64's command `5E` sets the former only. Despite
the decompilation field's `noBFlag` name, the native input routine uses this flag
to **enable** selecting the last option with B. It does not disable B.

When that last option is selected, the GameCube plays a short closing sound, or
a long closing sound when the second flag is set. The long form also sets message
status bit 11 to suppress the later duplicate message-closing sound. Other options
play the ordinary decision sound. Neither flag changes the closing animation's
geometry. The N64 sound IDs are `05` (short), `15` (long), and `0D` (decision).
The N64 retains its own sound API and timing; no GameCube audio data is imported.

## Native layout and hooks

Choice flags occupy bytes `B8` and `B9` of the unchanged `BC`-byte choice object.
The message's embedded choice starts at `1B0`. The choice initialiser at `80065064`
clears both bytes by widening its existing zero store at `80065128`. Other state,
including the twenty-byte text-storage references, remains unchanged.

The decision-sound call at `800667C0` passes its existing choice pointer to the
resident cancellation helper. Native disappearance setup and animation continue
unchanged. Message sound entries `8009FA18` and `8009FA38` retain their no-argument
calling convention and consult the singleton message window before emitting a
short or long sound. The message wait setup's final return at `800A28D4` becomes
a tail call that clears only bit 11. Initialisation clears that bit as well.

The native message subsystem does not otherwise test or set bit 11. Patches
require exact source instructions, linked helper bounds, and the normal external
interior-reference audit. Unknown command gaps remain rejected.

## Import and validation

Under the resident reference-presentation policy only, `62` compares with native
`5E` as the same B-button choice policy. Its sound handling must be fully installed
before that comparison is enabled. This does not permit adding cancellation where
the native message has none, changing choice counts or labels, or adding IDs beyond
the N64 bank. Storage and music menus with changed GameCube actions remain gated.

Tests cover both flag bytes and adjacent guards, command-index advancement,
B-to-last selection, ordinary A selection, all closing-sound decisions, duplicate
sound suppression, wait/initialiser flag clearing, native setup state, and retained
module guards. Emulator audio output remains disabled during all tests.
