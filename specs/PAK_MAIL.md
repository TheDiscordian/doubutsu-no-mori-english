# Native Controller Pak letter persistence

## Scope

The isolated fixture passes original passport and stored-letter note I/O,
including complete reading in a separate fresh process. It does not establish ordinary travel, letter-storage
menu operation, different-town identity handling, or original hardware support.
Snapshot generation remains disabled. Production code and save formats are
unchanged; generated fixtures and native evidence remain ignored under `build/`.

## Verified storage

All offsets and addresses here are hexadecimal. A one-bank Pak is `8000` bytes.
The native file-size table at `80116808` contains `1200` and `6700`.
Both notes begin with a sixteen-bit checksum whose complete-file word sum is zero.

The passport at `80137C40` contains the complete `BD0`-byte player at `08`,
the complete `528`-byte travelling animal at `BD8`, and a nonce at `1100`.
The ten full player letters begin at player offset `40A`, with stride `A4`.
The seven compact NPC letters begin at animal offset `10+2A`, with stride `B0`.
They retain the existing record sizes of `A4` and `84` respectively.

The stored-letter file contains eight ten-byte page labels at `02`, then 160
complete letters at `52`, arranged as eight pages of twenty records. The last
record ends at `66D2`, leaving 46 padding bytes through the `6700`-byte file end.
The native UI initializer at `8089BD4C` clears exactly these labels and records.
It also copies the player's ten pockets to a separate staging area at `6700`;
that staging area is not part of the persisted note. The overlay at VROM
`0079E430`, linked at `8089AD40`, is guarded with SHA-256
`afc2fe5337796bc9e2d50daacfb2ab23a56e241077273c7ec7cec7aa797f9235`.

## Native routines and fixture contract

`mCPk_InitPak` at `800790C0` opens controller zero and initialises native state.
`mCPk_SavePak` at `800793B8` copies the whole player/animal, checksums the
passport, and writes the note. `80079F44` reads and checksums that note;
`mCPk_PakPrivateLoad` at `8007942C` checks the private identity and copies the
whole player/animal into caller buffers. The latter is not a checksum validator.

The first letter-writer stage at `80079D50` checksums and writes the full `6700`
bytes. The fixture requires a local player and invokes only this stage. The
following stage calls the FlashRAM save pipeline and is deliberately excluded.
The native letter reader is `80079EA4`. Both notes use `8007920C`/`800792FC` and
the original `sCPk`/libultra routines. No fixture calls format, delete, or repair.

`pak_read_probe.s` is original test-only code, not a production patch. Its
144-byte independently assembled body locks the pad manager's serial queue,
reads all 1,024 blocks through native `__osContRamRead` at `800391B0`, then
unlocks on success or error. This exports the actual Pak before restoring an
emulator checkpoint, which can restore controller memory. The test allocation
is outside the resident module and is freed when validation completes.

The writer requires a fresh output directory, a matching-ROM isolated town,
an empty Pak reported by the native file counter, sufficient space for both
notes, and explicit `--allow-test-pak-write`. Existing user Paks are never write
targets. Both formats occupy all 177 slots with synthetic fixtures; complete
records, complete file checksums, six English reconstructions, and memory guards
are checked. The original live save payload must remain unchanged.

A separate fresh process receives only the exported Pak and a blank FlashRAM
control file. No town save, RTC, checkpoint, or RAM image crosses between the
two processes. Native raw reads must match the export before and after all
read-only file checks. The complete records and decoder checks run again.
Both processes restore their own checkpoints before ending. Detailed successes
and failures belong in the work log.

## Execution evidence

The writer passes 433 recorded steps, 189 native/test-probe calls, and 209
assertions. The native file counter changes from zero to two notes, and free
space changes from 31,488 to 512 bytes, consuming exactly the 121 pages occupied
by the two files. All 177 complete records, both complete note checksums, the
complete player/NPC import copies, and six English reconstructions pass.

The fresh reader passes 258 steps, 21 native/test-probe calls, and 208 assertions,
including the same 177 complete records and six reconstructions. Native chip
reads match the exported Pak before and after read-only checks. Both processes
preserve their complete live save payload, pass heap/stack/module guards, free
the test allocation, restore their own checkpoints, and exit gracefully.

The writer checkpoint restores its original empty Pak, so the writer's flushed
`test.pak` is not the persistence export. The separate native-read export is
the reader's input; the fresh reader's flushed Pak retains that exact content.
FlashRAM remains blank in both runs. The fixture does not claim ordinary travel,
normal storage-menu progression, or hardware validation.
