# Complete letter-editor recipient names

## Installed state

`build/letter-names-pilot` includes complete eight-byte English NPC recipients
while writing letters. The header and cursor use the GameCube English prefix
advances and eighty-pixel recipient allowance. Body/footer cursor behaviour,
editing acceptance, saved six-byte identities, and the ten-byte header stay
unchanged. The [specification](../../specs/LETTER_EDITOR_NAMES.md) records the
native offsets, source guards, relocation, and allocation.

Opening and closing compose the current header in an eighteen-byte temporary.
They do not read the persistent mail snapshot cache: new-letter initialization
does not reset that cache, so a reused board address must not revive old text.
Leaflet/fortune headers retain their native recipient-free animation. Read-mode
snapshot pagination and all five preceding reader hooks remain installed.

The board grows to 9,232 bytes, with 1,504 appended helper/constant bytes after
the materialized native BSS. Header/cursor frames are 112/56 bytes; the original
header frame is 128. The combined submenu reservation grows by 4,096 bytes to
247,168; its conservative requirement is 244,480. Neither saves nor the resident
module grow. The actual build still uses four MiB.

## Artifacts and reproduction

```sh
python3 tools/build_letter_names.py
bash tools/build_letter_names_pilot.sh
python3 -m unittest discover -s tests -p test_letter_names.py -v
```

- ROM: 33,554,432 bytes, SHA-256
  `785080e25caba10e4e0bc4557b84c6c08d23e47bbce0af70e097194db905c1de`.
- UPS: 5,132,326 bytes, SHA-256
  `a0173bc39c49f3188e9789a3dced5f7e7e29ec935e80dbd1e94efd936e753a2a`.
- Board image: SHA-256
  `6185a6ac26a5883497232c4ced9ae348ca6c9f1fe50bd9058de49c9f38848342`.
- Appended code/constants: SHA-256
  `cd5dea7d176245e0ed4f89c3f841dc4d8889f1505732a079209615fa333846e1`.
- Relocation: SHA-256
  `dea6b26c39d41bf5fd04a9530f5613e995823978a97deee85d1b05364252835b`.

Independent builds agree on the complete image, relocation, and manifest.
Generated assets, logs, ROMs, and UPS files remain ignored.

## Bounded verification

The two host checks pass in 0.160 seconds. Sanitizers cover full/short/fallback
names, identity bounds, colours and coordinates, header cursor/marker positions,
body/footer forwarding, invalid lengths/columns, fresh opening/closing headers,
native header-only types, and unchanged board/editor data. A failing snapshot
stub rejects any dependency on an earlier letter's persistent reader.

Four compiled/shared-install checks pass in 41.318 seconds. They verify pinned
code/imports/source profiles, two relocated allocation bases, retained native
cursor/marker and acceptance routines, rejected rehashed mutations, exact pool
instruction registers and signed-immediate arithmetic, and combined owner rows.
Both whole-cartridge/accounting checks pass in 134.257 seconds. Every preceding
payload is retained except the explicitly owned board, owner row, pool word,
DMA metadata, and checksum changes. The UPS reconstructs the complete ROM.
The combined counter verifies every required name reader, retains its original
751,284-character denominator, adds newly applied names only once, and rejects
damaged editor metadata or main-name symbols. Twelve counter unit tests pass.

The initial host fixture had a compiler-rejected eight-byte string initializer;
one corrected setup retry passes. Initial integration builds exposed two verifier
assumptions about the original board VROM and pool instruction. Both are replaced
with strict complete-variant verification, not skipped checks. Review then found
the stale-reader risk in the uncommitted animation prototype; current code removes
that dependency and passes its regression. Those prototype hashes are not release
artifacts. No emulator harness is constructed for this batch.

The [name-reader boundary](../../specs/DISPLAY_NAME_READERS.md) classifies saved
keys separately from display readers. Wider character names receive combined
translation credit only when every required installed route verifies. Remaining
item and catchphrase families are not credited merely because names are complete.

Ordinary letter editing and read/edit transitions, combined progression,
save/restart, and original hardware remain unverified. Existing unchanged loader
evidence is reused; it is not new editor gameplay evidence.

## Next implementation

Finish the remaining item-reader classification and any uncovered readers,
borrowed-catchphrase ambiguity, residual text/letters, and accents, then run the
bounded combined v0 smoke and hand over the base playtest patch. Keep the saved
identity and custom-input contracts intact. Title artwork and the GameCube-style
keyboard follow the base translation.
