# NPC reply generation bindings

## State and evidence

`tools/npc_mail_generation.py` checks seven complete original N64 functions,
six native selection/dispatch tables, five English executable functions, and
five English selection tables. It consumes the original ROM and supplied disc
locally. The functions are source contracts, not installed production hooks.
The [generation transaction](MAIL_GENERATION.md) provides complete field capture
and publication; these bindings identify where that API must be connected.

The source checks and selection/coverage tests pass. A separate
[complete word resource](NPC_MAIL_WORDS.md) verifies all 352 randomized phrases
against the supplied English and legacy sources. No ordinary NPC creator
currently generates English snapshot letters. Native word capture, complete
name capture, semantic template approval, loading/lifetime, and delivery
integration remain required.
An [exact saved-name mapping](NPC_MAIL_NAMES.md) supplies full names for both
known native Japanese and fitting English saved-name forms. Unknown names remain
unresolved; this source resource still needs native lookup and capture bindings.

## Whole-record boundaries

| Native function | Linked address | Required integration behaviour |
| --- | --- | --- |
| Composite whole-letter wrapper | `800A8B84` | Replaces assembly plus later header/footer copies as one operation |
| NPC reply field preparation | `800A8C48` | Captures original names, selected random IDs, and full English values before ten-byte truncation |
| Good reply creation | `800A8DB4` | Retains gift selection and the five already selected part IDs; propagates assembly failure |
| Bad reply creation | `800A8F30` | Retains selected classic ID; replaces temporary edge copies; reports failure |
| Reply metadata setup | `800A9028` | Retains recipient/sender identity, received status zero, mail type zero, and paper selection |
| Post-office submission | `800A9110` | Does not submit when creation fails; retains the native delivery result |
| Pending-reply processing | `800A91DC` | Clears local pending bits or the visitor reply only after successful submission |

Good reply creation calls the composite wrapper at `800A8F0C`, ignores its return,
and writes the gift at `Mail+24`. Bad reply creation calls the classic loader at
`800A8FD8` with header `80142E80`, footer `80142E98`, body `Mail+34`, and a stack
split output. It then unconditionally copies both edges and writes the split.
Changing only the lowest assembler cannot preserve a complete snapshot.

Metadata setup dispatches through `8010B890`, whose two entries are the bad and
good creators. It unconditionally writes received status at `Mail+26`, mail type
at `+28`, recipient identity/type, sender identity/type, and paper at `+29`.
Received status zero agrees with the native menu's Read path, but does not prove
that every other creator uses the same status.

Post-office submission uses the static whole record at `80142F80`. It checks the
five-letter queue capacity before calling metadata setup at `800A915C`, then
unconditionally submits to `800B6A3C` at `800A916C`. Unlike the English reference
wrapper, this native wrapper does not clear the staging letter first. A failed
new assembler must not expose the staging letter's older or partial text to
that unconditional submission.

The local reply loop checks return one at `800A92D0` before clearing the pending
bit at `800A92E0`. The visitor path checks at `800A9324` before clearing its reply
structure. Returning failure from submission preserves the native pending state.
This is an instruction-level contract, not a passing normal-delivery test.

## Proposed failure-return boundary

A new creator entry can take the existing six arguments and return the complete
staging-letter pointer on success, zero on failure. At the original submission
wrapper, the following guarded changes would propagate failure without replacing
the native receipt procedure:

| Address | Proposed instruction | Effect |
| --- | --- | --- |
| `800A915C` | Call the new creator | Existing stack argument in the delay slot stays unchanged |
| `800A9164` | `beq v0, zero, 800A917C` | A failed creator skips receipt and the later result copy |
| `800A9168` | `move a0, v0` | Delay slot supplies the complete letter pointer on success |

The original call at `800A916C`, send-type-zero delay slot, success-result copies,
and epilogue remain intact. The failure branch must target `800A917C`, not
`800A9178`: the latter would replace failure zero with stale register `v1`.
These instructions are a design only. Source-bound assembly, native calls,
allocation/loader failures, queue-full behaviour, unchanged pending state, and
ordinary delivery must pass before installing the gate.

## Capture ownership and selected fields

| Slot, decimal | Local reply source | Visitor reply source |
| --- | --- | --- |
| 0 | Player's saved six-byte name | Same |
| 1 | Complete display name of sender NPC | Exact saved-name recovery from reply `+4`; native lookup remains unimplemented |
| 2 | Name of the native-selected other NPC | Name of the native-selected local NPC |
| 3–13 | Eleven selected general-string values | Same families |
| 14 | Not supplied | Foreign town's saved six-byte name at reply `+A` |
| 15 | Not supplied | Current town's saved six-byte name |
| 16–19 | Not supplied | Not supplied |

The original preparation routine has one shared ten-byte temporary at `sp+40`.
Capturing that temporary after its loader returns cannot recover longer names
or words. Capture the selected NPC identity and random string ID before the
native loader or name helper truncates it. In particular, the foreign NPC name
does not carry a proven full identity in this reply structure; do not substitute
an unrelated current villager or guess a longer name from an ambiguous prefix.

Preparation does not clear every native free-string slot. The new capture must
begin a fresh generation lifetime so unused values from an earlier letter do
not become accepted substitutions. The full generated-letter transaction prunes
fields to the selected templates, but pruning alone cannot make stale required
fields valid. Saved/custom name fields retain their existing native formats.

## Random choices and reference mapping

Composite selection uses twelve 32-entry groups, one for each local/visitor and
six-personality pair. The local starts are `20,40,00,60,80,A0` hexadecimal; visitor
starts are `E0,100,C0,120,140,160`. Header, body A, body C, and footer each retain
their selected offset zero through 31. Body B uses offset zero through 15 plus
sixteen times the original gift gate. Gate zero selects a present; gate one does
not. Renaming the gate as a positive "has gift" flag would invert the template
half. The five original random draws must not be repeated.

Bad replies select `C5 + personality*3 + offset` locally or `D8 + personality*3
+ offset` for visitors, with offsets zero through two. Native ID `D7` is the gap
between these groups and is not selected by this formula. The English executable
has the same group tables, but matching groups do not independently approve
every translated sentence.

The eleven native word families each choose among 32 entries. Nine English
families retain the same base and size. Fish (slot six) moves from `0219` to
`06A1`, and insects (slot seven) from `01E5` to `0679`; both English families have
40 entries. The complete word resource confirms all 352 source/reference pairs
through exact full-value legacy agreement, including the first 32 fish/insect
entries. Its explicit slot/native-ID lookup preserves the selected creature;
it does not draw a replacement or use the eight added English entries. This
mapping still needs native capture integration and review in complete letters.

All available selectable reference parts use only fields provided by the
corresponding local or visitor preparation path. The coverage check includes
24 composite group/gift combinations and all 36 bad-reply selections. It finds
no missing field source slots. Composite footer `psz:004D` remains unavailable
in the current catalog because of unsupported glyphs. This check proves field
availability only: it does not approve full values, articles, wording, or every
cartesian combination of selected parts.

## Remaining acceptance

1. Connect the verified full-word mappings and resolve complete captured names,
   including stable foreign NPC identity recovery.
2. Approve selected template meanings and support the unavailable footer without
   changing existing catalog identities or shortening text.
3. Implement bounded loading and whole-record staging with explicit error returns;
   retain gift, RNG, paper, pending state, and queue-capacity behaviour.
4. Execute the failure gate and actual creator-to-receipt-to-reader path, including
   queue-full, unavailable resources, allocation failure, and repeated generation.
5. Validate normal play, saves/travel, old letters, and original hardware.
