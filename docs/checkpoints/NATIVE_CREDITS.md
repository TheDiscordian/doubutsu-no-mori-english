# Native credits work record

The implementation checkpoint adds 106 new ordinary-bank candidates and
source-correct provenance for four already-applied labels. All 110 native
credit rows have replacements. The full build contains 13,383 edits.
See the [current specification](../../specs/NATIVE_CREDITS.md) for exact inputs,
identities, caller changes, artifact hashes, and outstanding acceptance work.

The first silent run, `build/smoke-native-credits-01`, stopped at a fixture
assertion after loading and drawing the first page. The fixture incorrectly
expected RGBA values in glyph vertices. Inspection of the native font and
existing exact-vertex tests established that native vertex colours are zero;
the renderer emits RGBA through primitive-colour drawing commands. No production
patch changed in response. The fixture was corrected to check both zero vertex
colours and the actual primitive-colour commands.

The corrected run, `build/smoke-native-credits-02`, completed all sixteen pages,
all 110 loadable rows, 26 draws, 3,425 glyphs/texture loads, fade boundaries,
97 memory assertions, checkpoint restoration, and graceful shutdown. The
final cartridge/Pak files remained blank. The failed first run is not counted
as completed validation. Neither run establishes a normal K.K. performance,
GPU presentation, or hardware compatibility.

The full host batch passed 860 tests in 328.810 seconds. The final nine focused
credits tests passed in 4.147 seconds. Independent reconstruction confirmed
every installed edit, every untouched general-string entry, and the UPS round
trip. Main code differs from the shared-word pilot only at the credits actor's
VRAM-end word. All other changed DMA files belong to the credits actor,
relocation, general-string data/offsets, or DMA metadata.

The unrelated NPC-letter creator rejection remains deferred, not resolved by
this checkpoint. The next content work is fortune-slip letters and remaining
general-string consumers. Title artwork remains the first image task after
the main translation/runtime port.
