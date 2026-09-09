# Complete English home-gyroid default

## Source identity and presentation

The native saved default is general string `055C`, exactly 64 bytes, hash
`b3c40cd00dd3610400c2ff42cd922c63b7130720690e8abf30c16048a8eb7900`.
Two native initialisation paths load it into unchanged 64-byte saved fields:
`80094664` and `800C31FC`. No English import may overrun these fields or
silently shorten the default. Preserve custom messages and existing saves.

Do not use the supplied GameCube `055C` concatenation as the display source.
Actual GameCube home/start-data initialisation uses four entries `076A..076D`,
each followed by an explicit newline except the last line in start-data setup.
The four lines say: "Thanks for coming!", "Sorry I'm not in right now,",
"but please come in and", and "make yourself at home.". Keep their exact wording
and manual line boundaries. In particular, the third line differs from `055C`.
Joining the four complete lines with three native newlines requires 92 bytes.

Source checks must bind the supplied executable, both initialisation functions,
both four-ID tables, the four raw strings, the decoder, and the selected complete
gyroid introduction `message:0928`. Generated game text remains local.

| Supplied GameCube source | Bytes | SHA-256 |
| --- | ---: | --- |
| `title_game_haniwa_data_init` | 248 | `9fa8062669401a0d4fd0f7d32f67d12a0e0d120a86fcf5944d68631a0003d9c5` |
| `mHm_ClearHomeInfo` | 404 | `6404cdd7ab64390500512e851db95979844d5b3822880baf1587bab1f1f576b3` |
| `haniwa_msg$393`, `haniwa_msg$427`, each `076A..076D` | 16 | `2289fae58bcd3cdcef80b60480e55525b225967438962a33c41e31f04a2bb2bf` |
| `aHNW_set_talk_info_dance` | 168 | `3cb29237ab2ef9eba78d033517f1acae4af33572e68a64f3a51a48dbc042f4d4` |
| `string:076A` | 18 | `1ce29a8437f9bf90d493c0fb3ecf70cb21acf11418467d5395b2cf2698b79fba` |
| `string:076B` | 27 | `660598e5f0df373309b3bf0aa9aae222ceaaf006bd82b00a7a390d7aacd54142` |
| `string:076C` | 22 | `66525a02303e9802d9f89a14af415a5b36af487463128d215f1884cee4256b96` |
| `string:076D` | 22 | `c2a179432ae6a51715622dbf60fdf20fe011fd41bf88400412479c8e9c7306f3` |

## Actor-owned selection

The native `ovl_Haniwa` file is 6,800 bytes at VROM `0085F7D0`, linked
`8096AB90`, with a 448-byte relocation file at `00861260`. Its verified
`aHNW_set_talk_info_dance` routine spans `8096B2D8..8096B397`, hash
`53eeb84bdf79b90105d943cf3f3506c5473066590cbd892d05ac068e80d35f35`.
The five-state message table at `8096C458` is `0934,0935,0925,0928,092E`.
The other-owner branch formats saved text, then calls `mDemo_Set_msg_num` at
`8096B380`, with the selected message loaded in its delay slot. Its `sp+20`
contains the original home-gyroid pointer; the saved message begins at `+18`.

The selector in `overlays/gyroid_default/` changes only requested message `0928`
when all 64 saved bytes exactly match the original default. Every custom byte,
including padding, prevents substitution. Other requested IDs and null sources
retain the request without writes. The original setter still handles custom
messages. The assembly adapter reads the existing owner pointer, calls this
selector, and tail-calls the native demo-message setter with the selected ID.

Use `2AE7` for the complete default variant only with an atomic actor/text
installation. It is a native train-demo reserve, source hash
`0727aac8e3f598400dccbb8e9a23f39c10b3bc13e0dc1c168b93d03c0aa95609`,
with no script, relevant executable immediate, or aligned data reference in the
checked pinned sections. It is not allocated to a sequence; its existing
explicit English reserve-label approval must be reconciled when enabling the
variant. This is not proof against computed callers. Do not use `2AED`: despite
its zero scan hits, it contains actual scripted dialogue, not a reserve.

The variant preserves the complete approved English `0928` introduction and
its pauses, owner field `26`, page transition, outgoing `0929`, and final `01`.
Replace only its one `40` insertion with the complete four-line default.
The source `055C` is credited once only after both actual actor selection and
the complete approved variant are verified installed. Reusing an English
reserve gives no additional source credit. Never replace ordinary `0928`;
it must continue to show custom messages.

The current resident image uses the entire `6000`-byte linked allowance. Append
the small selector, adapter, and extracted native comparison data to the owned
Haniwa overlay, with audited relocations and updated actor allocation metadata.
Keep the resident image, native saved structures, current heap bounds, and
test scratch addresses unchanged. This is not a restriction against the
permitted Expansion Pak; this actor-owned feature does not need one.

## Installation and checks

`tools/gyroid_default.py` binds the original saved source, native initialisers,
actual GameCube functions/tables, decoder, raw banks, and all four English rows.
The 206-byte variant has SHA-256
`06130e75b09b9cf1cec54660524d30ce41e696c41ec334ac19d60ffb173bbdd4`.
Only its exact typed permit may replace the reserve's control stream. Ordinary
placeholder, capacity, and control validation remain strict for every other ID.
The complete original `0928` remains required. Candidate generation uses
`--english-gyroid-default`; cartridge builds require the matching actor directory
through the same flag. Missing, changed, or partial installations fail before
publishing a cartridge or mutating the caller's installation maps.

`tools/build_gyroid_default_actor.py` links a 6,976-byte actor: the unchanged
6,800-byte prefix except its one call, 76 selector instruction bytes, 36 adapter
instruction bytes, and the original 64-byte comparison data. No BSS is added.
VROM `03930000` holds the actor and `03938000` its 464-byte relocation file.
Main-code metadata at `80100DD0` changes only its first four allocation/DMA
words. Original profile, ownership flags, all 105 native relocations, and their
order remain. Four added rows cover the changed call, internal selector call,
and comparison-data high/low pair; the native setter tail jump stays absolute.
Appended instructions are independently checked against the exact intended
machine words, including their stack contract. Relocation checks cover the heap
start, a negative-low-half address, and the highest fitting four-MiB allocation.

`tools/build_gyroid_default_pilot.sh` builds the complete integration while
retaining every earlier resource. Independent Docker compilations agree. Eleven
host/source/ROM checks cover all 16,320 one-byte customisations, null/unaligned
inputs, original sources/guards, exact complete text, rejected altered permissions,
code/relocation mutations, atomic actor-only failure, previous-resource retention,
UPS reconstruction, and combined accounting. Seventeen sequence regressions pass.
Native evidence and remaining acceptance are tracked in the checkpoint.

Native acceptance must retain the original owner-state decisions, prove the
real adapter's stack contract, select custom/default paths correctly, load the
complete variant, preserve the original continuation, and restore saves, heap,
stack, and checkpoint. Full custom editing beyond the native 64-byte saved
capacity is not implemented by default substitution. The owner-message editor
must also present the English default; leaving the Japanese default visible
there is not a complete translation. Preserve explicit input limits and custom
text without truncation when implementing that route. The
[owner-editor core](HBOARD_EDITOR.md) provides its separate complete draft,
proportional layout, and save-safe confirmation; the owned overlay integration
remains required. Normal gyroid interaction,
save/reload, rendering review, and hardware remain broader acceptance work.
