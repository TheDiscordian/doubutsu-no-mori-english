# V3 speed-bag gameplay connections

## Implemented work

The speed bag has its real group-A stock entry, donor-order catalogue entry,
price/name, neutral feng shui properties, boxing HRA properties, English
score-letter name, and selected save dependency. ABI 49 enables the item in
the private development build only after those connections are installed.
Standalone component installation stays disabled. No original item or villager
is replaced, and neither web patcher offers V3 imports.

The complete English creator gains an additive boxing lookup row while
retaining all 55 original names. Five checked immediates and two relocated
name references change; the literal for template `37` stays intact. The
1,456-byte appended table expands its image to 62,656 bytes and full blob to
63,616 bytes, below the existing 65,536-byte image limit. Relocation records,
original template text, other dispatchers, and saved letter formats remain.
The loader's approved lengths and CRC bind the complete new blob.

Catalogue order is all 436 original entries, speed bag, haz-mat barrel, and
oil drum. The three new rows follow donor positions 175, 195, and 202. Speed
bag uses index 2260, mode zero, and price 2,990. Its additional row fits existing
alignment: the image/relocation remain 56,560 / 720 bytes. The menu needs
274,176 of its reserved 274,560 bytes; no extra pool allocation is introduced.
The native preview uses the real custom constructor and 9,216-byte model bank.

The group-A list appends speed bag after oil drum and before its terminator.
Counts are A 103, B 101, C 102; the pointer table moves to `394`, while the
whole goods resource remains 976 bytes. Native rarity mapping and RNG stay
unchanged. Feng shui reads the verified donor `0000` record, not another item's
colour or bonus.

## Current private artifact and save warning

`build/v3-speed-bag-gameplay-02/animal-forest-v3-asset-loader.z64`

- ROM SHA-256: `7c0cbcf9a5f0b8c13d2aa7cbd38f253a2864bd30e2027a23e29ccc0a29972a2c`.
- UPS SHA-256: `e5ee077a7ac33d3ae2e9220a67c97d03d95ec8496f5d8213acb47d0046ae77b1`.
- Complete creator SHA-256: `32f016a541f72567208680cc3fcbd717ec9c7ff03af8c7a7d870b3392102482a`.
- Selected-profile SHA-256: `b24cdb7030f3edfaa8852b94b202f7e2679c90b90347b650b63fd8ab17c0a508`.
- ROM 32 MiB; Expansion Pak required; permanent V3 prefix remains 48 KiB.

**The selected save profile changes.** Speed bag uses furniture bit 212:
profile byte 58, bit `10`. All other 192-byte profile contents are retained.
The saved format remains version 2, but saves written with this profile require
a build containing this dependency. Earlier builds without it reject them.
The decoder accepts adding support, but ordinary cross-build reload has not
been newly verified. Preserve backups; never load V3 saves in V2 or an
incompatible earlier V3 build. User saves and previous cartridges stay untouched.

## Executed evidence

`build/v3-speed-bag-gameplay-tests-01.log`: six checks pass for the connected
ABI 48 component build. They cover complete creator/loader reconstruction,
unchanged original name keys and template literal, damaged-source/configuration
rejection, actual stock and catalogue entries, capacity, exactly one additional
profile bit, neutral feng shui, complete composition, UPS reconstruction, and
the exact import-free V2 result.

The actual save codec runs with address/undefined-behaviour sanitizers. All
four rotations share the correct item identity; all four residents record
ownership independently. Complete bank encode/decode retains state. Removing
the dependency returns the missing-profile error without modifying the output;
adding another dependency retains existing ownership. No FlashRAM I/O is used
by this host check.

`build/v3-speed-bag-gameplay-native-02/`: **149 records / 103 assertions pass**,
including checkpoint restoration and graceful shutdown. The combined run
executes the real native paths with the exact installed item flag temporarily
enabled:

- Group-A rarity queries, complete stock selection, exactly one RNG draw,
  category rejection when disabled, ordinary pocket-acquisition entry, and
  the correct independent ownership bit.
- Complete English HRA generation and full restored text for both boxing
  templates, an original exotic-series letter, and a speed-bag item
  recommendation. Borrowed inputs stay unchanged, unknown names cannot
  partially write a letter, and the creator detaches after every call.
- All 439 catalogue entries, complete English names, all three model transfers,
  real speed-bag construction resolving both rig headers and the complete
  initial pose, native preview-buffer switching, completion indication, and
  original-item fallback.
- Complete code/resource retention, memory/save guards, no faulted thread,
  restored fixture state, and no physical audio output.

The initial run establishes stock/ownership, then refuses a test proof that
overlaps the resident module before calling the letter loader. The one setup
correction checks the entry directly and uses the debugger's existing module
call route; the cartridge code does not change for that retry.

The enabled ABI 49 artifact preserves the native-tested gameplay code and
resources. Only the item flag, ABI header/startup comparison, and matching
startup configuration differ. `build/v3-speed-bag-gameplay-tests-03.log` records
all seven current checks passing, including complete reconstruction of those
differences. Its first added retention assertion omitted the compiled startup
ABI comparison; the expectation is corrected, not the ROM. The minimal
current startup check in `build/v3-speed-bag-live-native-01/` passes all
12 records and eight assertions: initialized startup, enabled item, complete
selected/copied dependency, expanded profile pointer, both guards, and no fault.
The isolated emulator shuts down gracefully with audio disabled.

## Surface review and remaining work

Both donor boxing surfaces at index 65 have no complete pixel match among
the 68 native wall/floor records. All 8,192 wall pixels and 16,384 floor pixels
are compared after conversion. The checked cached banks match the supplied
archive SHA-256 `b3d784fbb993e83f65ce4b904db2cd6e42f6cf08e8467a77f2c8614d395e362a`.
Their converted row hashes are
`4d4ed5136bf65bdd812f67a3034e13c7d8e319cd35730c44ea5db03739fa38f8` and
`642ee5b3f863130e9ae8b034d40b31799ee8519825f47d6b5ecd428098c8c1fb`.
The explicit no-match HRA surface value is therefore appropriate until those
optional surface imports are implemented; no native wall/floor is substituted.

Ordinary shop purchase/payment, placed interaction and final GPU appearance,
ordinary speed-bag save/restart, and original-hardware acceptance remain open.
The private item is available for those checks; component success is not a
complete lifecycle or hardware claim. Punchy's house/default integration is
next, including a checked relocation for his additional foreground layers.
Both served patchers, main, deployment, services, visibility, and the released
trailer remain unchanged. The user tests V3 and explicitly approves any future
patcher switch; GitHub source tracking continues on `v3/optional-imports`.
