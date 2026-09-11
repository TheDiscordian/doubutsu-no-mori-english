# Native item-name fixture follow-up

Two selected tests pass in 3.158 seconds, closing one historical fixture error
and checking the complete current RC4 item-name resource. No production source,
approval, translation, ROM, or saved data changes. There is no new emulator or
hardware execution, and the full suite is not declared passed.

## Historical resource versus current importer

The early `native-items-pilot` has a frozen 3,563-edit resource. Later native-item
identity approvals reject some older donor metadata, so rebuilding that early
resource with current import permissions is not a valid archive-retention check.
The test now binds the exact historical manifest/resource, reconstructs every
stored field from its recorded complete translation and actual native source,
and preserves all prior ROM/UPS/unchanged-file and retained-edit assertions.
It explicitly asserts that the production importer still rejects the obsolete
metadata. No historical permission is added to the production builder.

Bound old resource SHA-256:
`69e7bf2e099e652463deecd3a1416f09774c9b4b4810bfc3cfd104956eff4add`.
Bound old manifest SHA-256:
`4546a33ca0ce19089192eefb7abf94107b20ebab2219360395e0f111bbee19a7`.

## Current installed names

The new current-artifact check calls the real accented-resource builder, which
validates all 4,536 preceding edits and the eight complete accent fields. Its
entire output matches RC4's installed `02A00000` resource. All 43 source-bound
N64-specific original names appear in their 128 rotation/alias fields with the
required project provenance and complete wording. The 45 names fitting native
ten-byte fields also match the actual installed short-name bank.

Current pre-accent resource SHA-256:
`ff138b625616f972118d66623804d509082d7f98d3e02704ccf8f99e1f283af3`.
Complete installed resource SHA-256:
`693ef2c0749822d07062114ffff0b35b4bb8a56d3b2617c932d9220dcc92165b`.
Checked RC4 ROM SHA-256:
`5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.

```sh
PYTHONPATH=tools:tests python3 -m unittest \
  test_native_item_names.NativeItemArtifactTests.test_complete_installed_names_retention_resources_and_ups \
  test_native_item_names.CurrentNativeItemArtifactTests -v
```

Both tests pass without skips. The older combined counter/scenario method is
not selected or changed; its separately recorded error remains unresolved.
The completed archived native execution, other item families, and unchanged
source-schema tests are not rerun. Current resource checks do not establish
ordinary appearance, every name consumer, save round trips, or hardware acceptance.
