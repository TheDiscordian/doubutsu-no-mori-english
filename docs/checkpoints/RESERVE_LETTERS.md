# Reserve letters and sender-only signatures

## Installed result

`build/reserve-letters-pilot/animal-forest-halfwidth.{z64,ups}` applies all fifteen
parts of the five reserve letters. Each part reads `Extra`, preserving its
original blank lines. The English donor retains Japanese body bytes; the body
word is an original translation matching the donor's English header and footer.

- ROM SHA-256: `648d59503d8bf0c6031f24efc02fc2cdca99e0e4a10cd05d5a663b66e6ee3bda`.
- UPS SHA-256: `8ef50a32f585a175271993f1f280a62ccba892036c198524997c603e2d0f3939`.
- Rebuild: `python3 tools/reserve_letters.py` with the exact general-string predecessor.

Only three text banks and their tables change. The body file extends by sixteen
bytes, with fifteen final padding bytes protecting the native reader's rounded
DMA request. The virtual base, native loader code, all other records/resources,
font pixels, immutable catalogues, and saved formats remain unchanged. Cartridge
size remains 32 MiB with the existing four-MiB runtime configuration.

## Verification and accounting

All three focused tests and sixteen fast counter tests pass. Checks cover exact
source/reference wording, line counts, capacities, every retained row, all
rounded bank reads, the final bank entry, complete cartridge/resource/index
retention, UPS reconstruction, source-bound omissions, and installed accounting.
Unchanged native code reuses prior evidence; no extra native harness is required
for these data-only changes. Ordinary progression and normal save/restart remain
in the combined v0 smoke.

The fifteen newly installed parts replace thirty source characters. The counter
also recognizes eleven already-installed sender-only signatures, correcting
credit for thirty-five source characters. Those exact English signatures omit
Japanese sign-off words while retaining their dynamic sender command. The
exception binds source identity, encoded command, and the complete NPC/quest
creator route; arbitrary empty or unselected parts receive no credit. Historical
counter expectations include that same correction consistently.

The focused installed measurement verifies 750,240 replaced source characters
out of 751,284. The next implementation is the eighteen retained classic
variants in [their specification](../../specs/CLASSIC_LETTERS.md). Candidate
code does not count as installed translation. Three zero-filled tail slots remain
structural storage and must not be overwritten with English filler.
