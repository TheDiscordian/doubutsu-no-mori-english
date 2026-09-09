# Complete house-sign names

## Installed state

`build/house-name-pilot` displays complete eight-byte English villager names
when examining house signs. The [specification](../../specs/HOUSE_NAME.md)
records the exclusive lookup caller and existing safe stack destination.
The preparation blanks all eight bytes before lookup; an unmatched house or
failed coordinate conversion cannot expose uninitialized stack text.

The actor remains 512 bytes, its relocation remains 64 bytes, and no allocation
or saved field grows. The coordinate lookup, resident selection, message `1369`,
field zero, window colours, camera/listening state, and timing remain unchanged.
The shared identity bridge and complete dialogue fields are the exact versions
already exercised by the conversation-name native batch. The actual build still
uses four MiB.

## Artifacts and reproduction

```sh
bash tools/build_house_name_pilot.sh
python3 -m unittest discover -s tests -p test_house_name.py -v
```

- ROM: 33,554,432 bytes, SHA-256
  `215f47476f21d80b6ea30ea4fda5d32a8408d3d47638b854db8dfc6597299450`.
- UPS: 5,130,473 bytes, SHA-256
  `21848ae3eb627f6a23e5e5f8ffc335ede91b0d769ecb81e9d90068c531a33b15`.
- Actor: SHA-256
  `135daf6a3d3e3e907fd1f8e9bdea1c852f0e8cc56c385b58844b8be2ae2b4b68`.
- Unchanged relocation: SHA-256
  `7d185e9b992f99a24ea80cbd0e2d5083904ca3594bcc05674e40c68c327edb8c`.
- Position lookup with approved display call: SHA-256
  `bdceaa65d1c2e1d0218f633ba939394e7439619c467c405d85c3fd65ea63231b`.

## Bounded verification

All six focused tests pass in 68.513 seconds. Independent pinned MIPS assembly
matches the exact preparation, length, and display-call words. Source checks
verify both initialized words, unchanged argument values, the callee's own
argument-home stores, frame bounds, field and message IDs, and retained lookup
instructions. Relocation at two allocation bases preserves the fixed calls.
Failed dependency guards leave proposed changes unpublished.

The native-reference audit finds exactly one lookup caller and no aligned
literal pointers or external branches into the changed preparation. Complete
cartridge checks retain every previous translation payload and the full
conversation/secret-letter integrations, and reconstruct the ROM from the UPS.
Twelve counter tests pass; installed house-reader verification adds no duplicate
source-name credit. Four source/assembly tests also pass while the initial build
runs; the two cartridge tests are skipped until the complete six-test pass.

No new emulator harness is needed for unchanged shared helpers. Their evidence
remains the recorded conversation-name batch, not new house-sign gameplay.
Ordinary house-sign interaction, combined progression/save/restart, and original
hardware remain unverified. No testing-setup failure or retry is needed.

## Next implementation

The letter-writing screen still uses the native saved six-byte recipient name.
`runtime/mail_view_hooks.s` sends read-mode headers to the full-name renderer but
retains the original editor header routine for edit mode. Complete that display
and its cursor geometry without widening the saved recipient or losing edit
behaviour. The random fishing-name generator and ordinary mail-identity setter
are saved-data writers and must retain their six-byte contracts. Continue other
remaining item readers, borrowed-catchphrase ambiguity, residual text/letters,
and accents before the combined v0 smoke.
