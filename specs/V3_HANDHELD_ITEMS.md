# V3 held equipment

## Representation and scope

The player's held model, the dropped inventory item, and its catalogue preview
are distinct representations. Use the donor's actual selectors for each one.
The room/collection context records in [the shared pipeline](V3_FURNITURE_PIPELINE.md)
govern drop semantics; a prepared catalogue model is not a usable handheld item.

`tools/v3_handheld_items.py` discovers equipment dependencies from five complete
GAFE01-r0 functions: item-to-equipment-kind, kind-to-shape, kind-to-animation,
resource-pointer lookup, and resource-type lookup. Function code, paired table
relocations, complete table spans, pointer ownership, switch-return targets, and
index bounds are checked. Counts and mappings come from those functions/tables,
not a maintained list of tools. Names and hashes come from `itemName_tool`.

The 92-entry item switch selects 79 equipment identities/states and rejects
`222C..2238`. Thirty-six ordinary tool/umbrella IDs occupy `2200..2223`;
eight custom umbrellas occupy `2224..222B`. The remaining selectors cover golden
tools, worn axes, balloons, pinwheels, and fans. The complete shape/animation
tables have 80 bytes each, including the donor sentinel; the resource pointer
and type tables contain 50 records each. Preserve animation indices even where
the selected static model does not consume an animation.

The shared donor inventory attaches these dependencies to its existing item
records, without adding duplicate identities or enabling import choices.
Worn axe IDs select three different ordinary-axe appearances. They remain
states of one parent, not separate selectable items. Their collection display
can be shared while their held shapes and room-drop IDs remain different.

## Shared conversion

The existing pipeline accepts `--representation handheld`:

```sh
python3 tools/v3_furniture_pipeline.py scan --representation handheld \
  --output build/held-scan/inventory.json
python3 tools/v3_furniture_pipeline.py convert --representation handheld \
  --assets-only --output build/held-assets
```

`--select` filters by donor inventory ID. Shared model roots are converted once;
each output records every selected parent/state that uses it. The supported
category is `static-held-model`. Unknown or unsupported selections reject before
creating output. `import` and conversion without `--assets-only` reject because
native player integration remains unfinished.

`prepare_models` and `compile_models` are shared with furniture conversion.
Both front ends use the same dependency tracing, complete texture/palette/vertex
conversion, material checks, triangle conversion, native graphics compiler,
alignment, and model-list assembly. Static held models introduce no simplified
mesh, replacement texture, dropped layer, or item-specific emitter. The prepared
objects use segment six; an eventual owner must explicitly establish and restore
the correct graphics bindings. No cartridge allocation or native profile is
implied by a prepared object's model-root description.

Nineteen held item/state records use fourteen static model roots: eight fans,
ordinary/golden shovels, and four axe appearances. Twenty records use animated
skeletons; forty umbrellas use a separate owner and no model root from this
table. Neither group is converted into a static substitute. Prepared output has
the distinct `AFV3-HANDHELD-PREPARED-ASSETS-1` format, which the furniture installer
rejects. Runtime and save-profile selection remain off.

## Native integration work

The current native player equipment selector is `808BD3F8..808BD583` in owner
VROM `007AC420`, linked at `808B2D50`. Its 396 bytes have SHA-256
`3e1e9584685cef3dcb81e6fe99ef412ddc49fd4a8df74901f55b1742f234258b` in both the
original and current ABI-96 cartridge. It reads ordinary saved equipment at
player-private offset `3EC`, or title-demo equipment at controller offset `3C`.
It accepts only `2200..2223`, using a 36-entry jump table at `808E0274` with
SHA-256 `b46dbe4b89cb5647022dddcf27baa8e2ca8ea5ffc73c02a249f32b3c695c6af1`.
The extra donor handheld IDs are therefore not existing native player support.

The next implementation must extend equipment selection and all dependent
kind-indexed readers without changing original kind meanings or overstepping
signed-byte bounds. Add selected model ownership/loading, safe cleanup and
graphics bindings, take-out/put-away, and actual per-category actions. Do not
route a fan through an unrelated umbrella or ordinary tool action.

For fans, the donor implementation is in `m_player_item_fan.c_inc` and
`m_player_main_swing_fan.c_inc`. Its draw entry is `.text:173A84`; setup and main
action entries are `.text:1962B0` and `.text:1965A4`; the controller check is
`.text:164628`. The full player wait/swing animation descriptors are
`.data:16A2A8` and `.data:16A49C`. Those animations, the split-body fan mask,
button/timing behaviour, and sound still need native integration. The prepared
held graphics alone do not implement them.

Inventory/ground readers, official names and prices, acquisition, context-correct
catalogue/collection integration, optional selection, and save/profile handling
remain required before enabling new handheld items. Original tools must not be
duplicated as new imports. Preserve existing ROMs/saves and both V2 patchers.
