# Native keyboard direction commands

The shared grid emits the original editor's command numbers, not an independent
direction enumeration. The original selector at `8088537C` combines held and
triggered buttons, then maps the four C-button masks as follows:

| Controller mask | Direction | Native command | Return instruction |
| --- | --- | --- | --- |
| `0001` | Right | 1 | `808854B8: 24020001` |
| `0002` | Left | 2 | `80885488: 24020002` |
| `0008` | Up | 3 | `808854A8: 24020003` |
| `0004` | Down | 4 | `80885498: 24020004` |

Commands 5–8 retain Done, Backspace, Exchange, and Insert. Grid direction state
uses the same corrected enumeration consistently; D-pad/stick movement remains
internal, and only C-buttons emit cursor commands. Numeric regression assertions
are independent of the implementation's enum names.

## Compiled correction

`core.h` defines the native order explicitly. The pinned toolchain emits a
12-byte-shorter controller. The linker pads its original `5A80..5FD7` reservation
to retain every following bridge, hook, table, hint, and private-state address.
The overlay remains 28,656 bytes; the relocation file remains 2,096 bytes. Native
owner metadata, allocation, saved fields, and all prior editing code are unchanged.
Only the controller reservation and its relocation records differ.

The source-compiled version-two image is
`3f1c6fd50c06695d114dcd94785c26f80408493c74b7c4ccd8f644746c46c00c`.
With native-encoded control hints, the installed image is
`d087dd33e57659e933b88f4d41bbe2a05623a07fb09a41ee7b98737e21f25579`.
The relocation hash is
`6fc26aa496a5407b0af08239d0cf85c8cb5c602dc269fe85ad54699b8c01597f`.

Validation selects only an exact reviewed image/profile pair. Both original and
corrected compiled images retain their own source and relocation identities;
mixing versions or changing unknown instructions fails. Version-one source
evidence reconstructs its two reviewed header/linker differences explicitly,
while every other source hash is checked against the current unchanged file.
The post-v0 rebuild can compile that version-one intermediate from these exact
two source transformations in an ignored compiler folder. Normal compilation
still defaults to version two, and the rebuild's final hash/installed-grid guard
requires the corrected version. Replay intermediates are not playtest outputs.
Native hint encoding reverses only the reviewed three data bytes before compiled
verification; it does not hide a code change.

## Focused native evidence

The isolated empty-name checkpoint belongs to the exact older
`title-nookington-combined-01` ROM. It must not be relabelled as a checkpoint of a
new cartridge. The correction probe verifies the loaded controller against the
original relocated image, writes the independently compiled corrected controller
into only that reservation, and verifies its full readback. Every address outside
the controller reservation remains identical. The checkpoint is restored before
shutdown; no user save is involved.

Controller holds use ares' existing Frame Advance hotkey, separating host polling
time from emulated frames. Four requested frames held and four released keep the
test below the eight-game-frame repeat threshold. These are emulator frame
requests, not a claim that every request runs a full native 30-Hz game update.
The test checks normal name-entry handlers, not injected text or direct handler
calls. Cartridge installation/relocation is verified separately against the new
ROM and complete resource chain.
