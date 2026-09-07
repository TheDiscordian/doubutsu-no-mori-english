# NPC stored-letter display callers

## Scope

Three direct calls to the native compact-letter reverse converter lead to the
letter window from NPC dialogue. The first-job handler and the two branches of
the ordinary handler pass isolated caller-level native validation. The standalone
reverse-conversion tests establish preservation of the compact text and metadata,
not successful execution of these callers or normal NPC interaction.

These paths are prerequisites for snapshot generation. Generation remains
disabled; no new save representation is approved by this audit.

## Native callers

All addresses and field offsets in this section are hexadecimal.

| Caller | Overlay VROM / linked RAM | Handler range | Reverse calls | Window call | Temporary letter |
| --- | --- | --- | --- | --- | --- |
| First job | `00814FA0 / 8091CB30` | `8091D3E0..8091D484` | `8091D428` | `8091D448` | `8091D660` |
| Ordinary, known sender | `00815B70 / 8091D7B0` | `80921618..80921704` | `80921678` | `809216CC` | `80921E90` |
| Ordinary, unknown sender | Same | Same | `80921690` | Same | Same |

Both handlers clear their complete temporary `Mail_c` using `8009C384`, call
`mNpc_AnimalMail2Mail` at `800A8344`, and open submenu program twelve through
`800C4DB0` with read mode one, argument zero, and the temporary letter as the
fifth o32 argument. The letter resides in overlay BSS; its lifetime must extend
through window close, not merely through the opening call.

The manager's `174` field supplies the submenu pointer; `178` points to the
client pointer, and the client's `174` field supplies the animal identity.
The manager's `17C` points to the sender-memory pointer. The first-job handler
uses the compact letter at memory offset `2A` and passes the memory's leading
player identity as sender. It sets manager bytes `185/186` to `4/10` and starts
the continuation message stored at `1A0`.

The ordinary overlay globals at `80921DE8/80921DEC` hold the known-memory
indicator and compact-letter pointer. The known-sender branch obtains the
actual sender identity through manager `17C`; the unknown branch passes a null
sender. Both explicitly clear temporary mail type at `80921EB8`. The unknown
branch also fills the six sender-name bytes at `80921EA2` with spaces via
`8009992C`. This operation does not touch the 122 text bytes. The ordinary
handler sets manager bytes `185/186` to `4/3` and locks message continuation.

The recipient is the NPC in both handlers. The read-only header must therefore
use its complete English display name, while sender and town identities retain
native saved capacities. See [recipient resolution](MAIL_READER.md#recipient-display-names).

## Relocation and source bounds

The verified retail ROM is the authority; the matching reference source is
useful for names but does not substitute for N64 instructions.

| Overlay | File bytes | BSS bytes | Relocation VROM | Relocation bytes | Text / data / rodata bytes | Entries |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| First job | 2,864 | 176 | `00815AD0` | 160 | 2,784 / 80 / 0 | 33 |
| Ordinary | 17,968 | 352 | `0081A1A0` | 2,240 | 16,768 / 1,200 / 0 | 552 |

The original loader must zero BSS and relocate references into the complete
file-plus-BSS range. Pelly's relocation model is restricted to a different
overlay with no BSS and is not a valid substitute for these two layouts.

First-job overlay SHA-256:
`3da47017db9ccc53be92f9afdd71d48a364ba172832cdfadc1a60ca4f6f54a8c`.
First-job relocation SHA-256:
`7589cd6d6e9138065042c2652b079624035e3c60f856ed4e44765515a8f01f23`.
First-job handler SHA-256:
`4c81b5c98648b592d3cc38433f246c79cdc922dc1636c90ab0208984096163eb`.

Ordinary overlay SHA-256:
`4d7822e44c34b224c6e6cb8374407ebe1c3b56279e19ab3eee0932d3b8ca9320`.
Ordinary relocation SHA-256:
`88122500ea6e119be5ac7fc89f3091df1fdaac6b0496f983aa0abd4cc5f0688c`.
Ordinary handler SHA-256:
`cd9440a8f9606c7820fb4b0b06c913753d7aff1b2e327b20fc9e1783994e8755`.

## Required native checks

Use silent isolated checkpoints and the verified graph-thread call boundary.
Load each original overlay with the native loader; independently compare its
relocated instructions, data, and zeroed BSS before executing any handler.
Allocate and guard synthetic manager/client/memory records without modifying
ordinary progression or NPC memories. Test all three branches with both
snapshot kinds and ordinary letters. Check the complete temporary letter,
recipient identity, unknown-sender clearing, source retention, board mode,
full decoded output, all rendered pages, and successful window close.

Keep the overlay allocation alive until close, then free it and restore the
complete checkpoint. Normal actor selection, animations, subsequent dialogue,
delivery, game saves, and hardware still require their own validation.

## Isolated caller harness

`npc_mail_show_test_scenario.py` verifies the installed full reader and selects
one long classic letter, one long composite letter, and an ordinary synthetic
letter. `npc_mail_show_smoke.py` executes all three through each caller branch.
It does not replace the handlers or their conversion/window-opening calls.

The heap fixture contains the complete overlay and BSS, relocation scratch,
manager, client, NPC identity, sender memory, compact letter, and guarded full
letter comparison buffers. The independent relocation model accepts only the
two exact original overlay/relocation pairs and permits targets within their
file-plus-BSS bounds. The native loader must match that complete expected image
before any handler call. Host tests cover several heap bases, unchanged
non-relocated bytes, complete pointer relocation, zeroed BSS, rejected altered
files/tables, and invalid or out-of-bounds destinations.

The handler's full temporary letter is compared with a separately executed
native conversion, including the unknown-sender name clearing. Compact source,
player state, and saved NPC population must remain unchanged during the call.
After live rendering and close, source letters and saved header/footer
preferences must remain unchanged. Normal frame updates are not misclassified
as caller mutations of unrelated saved NPC state.

Snapshot cases verify every page and glyph position in the real window.
Ordinary cases verify complete source retention, body/footer lengths, and
entry into each installed header/body/footer hook; the separate ordinary-view
regression supplies full glyph-position checks. Each overlay allocation is
freed only after its last window closes. A complete emulator checkpoint restores
the machine after the full run. Passing these isolated calls is not a normal
NPC actor interaction, save/reload, or hardware result.

The complete native run passes nine windows: ordinary letters and both
snapshot kinds through each of the three branches. It records 45 native calls,
151 memory assertions, three complete relocated/BSS images, and three frees
after window close. Six snapshot windows cover twelve pages, 1,713 glyphs, and
6,852 vertex positions. The ordinary windows reach all three installed draw
hooks with complete retained source records and expected body/footer lengths.
All 510 steps finish with checkpoint restoration, blank FlashRAM, and graceful
shutdown. No production patch to either NPC show overlay is required.
