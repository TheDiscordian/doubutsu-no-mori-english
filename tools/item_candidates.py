"""Complete reference item names within the unchanged ten-byte native fields."""

from collections import Counter

from aflib import sha256
from textcodec import LATIN, encode, tokenize
from textvalidate import validate_entry
from item_matches import identity_key, verify_source

ITEM_WIDTH = 10
REFERENCE_WIDTH = 16
FURNITURE_COUNT = 947


def item_candidates(bank, inventory, references, info, skip_ids=(), *, capacity=ITEM_WIDTH, matches=None, originals=None):
    if capacity not in (ITEM_WIDTH, REFERENCE_WIDTH):
        raise ValueError("Unsupported item-name candidate capacity")
    source = bank.entries()
    if bank.name not in [f"item_{g:02X}" for g in [0x10, *range(0x20, 0x30)]] or bank.fixed_size != ITEM_WIDTH:
        raise ValueError("Unexpected native item-name layout")
    furniture = bank.name == "item_10"
    if furniture and len(source) != FURNITURE_COUNT*4+1:
        raise ValueError("Unexpected native furniture-name count")
    def indexed(rows):
        result = {}
        for row in rows:
            if row["id"] in result:
                raise ValueError("Duplicate item-name input ID")
            result[row["id"]] = row
        return result
    inventory, references = indexed(inventory), indexed(references)
    matches = {} if matches is None else matches
    originals = {} if originals is None else originals
    if matches.keys() & originals.keys():
        raise ValueError('Native and donor item-name approvals conflict')
    for id in {*matches,*originals}:
        if id.startswith(bank.name+':'):
            index = int(id.split(':')[1], 16)
            if index >= len(source)-(1 if furniture else 0) or identity_key(id) != id:
                raise ValueError('Item identity approval has an absent or non-root native slot')
    edits, manifests, remaining, counts, identities = [], [], [], Counter(), set()
    count = FURNITURE_COUNT*4 if furniture else len(source)
    for index in range(count):
        id = f"{bank.name}:{index:04X}"
        reference_index = index//4 if furniture else index
        reference_id = f"{'furniture' if furniture else bank.name}:{reference_index:04X}"
        original_name = originals.get(identity_key(id))
        match = original_name or matches.get(identity_key(id))
        if match:
            verify_source(match, source[index], info)
            reference_id = match['reference_id']
        legacy_id = f"{bank.name}:{reference_index:04X}"
        if furniture and source[index] != source[index//4*4]:
            raise ValueError("Native furniture rotation names differ")
        if id in skip_ids:
            counts["original_draft_override"] += 1
            continue
        row, reference = inventory.get(id), references.get(reference_id)
        if original_name:
            reference = {'id':match['reference_id'],'text':match['translation'],
                         'source_sha256':match['reference_sha256']}
        if match and (not reference or reference.get('source_sha256') != match['reference_sha256']):
            raise ValueError('Missing or stale approved item-name reference')
        if not row or row.get("source_sha256") != sha256(source[index]):
            raise ValueError("Missing or stale item-name inventory")
        if row.get("legacy_entry_id") != legacy_id:
            raise ValueError("Unverified legacy item-name donor mapping")
        reason = None
        if not reference or not reference.get("text"):
            reason = "missing_english_item_reference"
        elif not match and row.get("legacy", "").strip().casefold() != reference["text"].casefold():
            reason = "item_identity_not_confirmed_by_legacy"
        else:
            encoded = encode(reference["text"], info)
            if len(encoded) > REFERENCE_WIDTH or sha256(encoded.ljust(REFERENCE_WIDTH, b" ")) != reference["source_sha256"]:
                raise ValueError("English item-name reference hash mismatch")
            if any(t.kind != "text" or t.data[0] not in LATIN for t in tokenize(encoded, info)):
                raise ValueError("Item name must contain only supported plain Latin text")
            if len(encoded) > capacity:
                reason = "full_reference_name_exceeds_native_ten_bytes"
        if reason:
            counts["rejected"] += 1
            remaining.append({"id": id, "reference_id": reference_id, "reason": reason})
            continue
        # The sixteen-byte mode feeds a separate resource, never the native bank.
        validate_entry(source[index].ljust(capacity, b" "), encoded, info, bank.name)
        edit = {"id": id, "source_sha256": row["source_sha256"],
                "translation": reference["text"], "control_policy": "exact",
                "provenance": {"source": "user-supplied GAFE01 revision 0 disc",
                               "reference_id": reference_id, "reference_sha256": reference["source_sha256"],
                               "legacy_entry_id": legacy_id,
                               "match_basis": "rotation_index_name_confirmed_case_insensitive_by_legacy"
                               if furniture else "same_id_name_confirmed_case_insensitive_by_legacy"},
                "status": "mechanically_validated_candidate_not_reviewed", "adaptations": []}
        if original_name:
            from native_item_names import SOURCE
            edit['native_item_name'] = original_name['id']
            edit['provenance'].update(source=SOURCE,match_basis='reviewed_native_original_translation')
            edit['status'] = 'source_reviewed_original_translation'
            counts['native_original_candidates'] += 1
        elif match:
            edit['item_reference_match'] = match['id']
            edit['provenance']['match_basis'] = 'reviewed_native_item_identity'
            counts['reviewed_identity_candidates'] += 1
        edits.append(edit)
        manifest = {k: v for k, v in edit.items() if k != "translation"}
        manifest.update(encoded_bytes=len(encoded), encoded_sha256=sha256(encoded),
                        stored_bytes=capacity, stored_sha256=sha256(encoded.ljust(capacity, b" ")),
                        layout_issues=[], expanded_bound=len(encoded))
        manifests.append(manifest)
        counts["accepted_candidates"] += 1
        identities.add(reference_id)
    report = {**counts, "source_entries": count, "storage_slots": len(source),
              "excluded_filler_slots": len(source)-count, "accepted_reference_identities": len(identities),
              "remaining_by_reason": dict(Counter(r["reason"] for r in remaining))}
    return edits, manifests, remaining, report
