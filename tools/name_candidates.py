"""Bounded English villager-name candidates with unchanged native storage."""

from collections import Counter

from aflib import sha256
from gc_text import plain
from textcodec import LATIN, encode, tokenize
from textvalidate import validate_entry

NPC_COUNT = 216
NPC_WIDTH = 6
REFERENCE_WIDTH = 8


def npc_candidates(bank, inventory, references, info, skip_ids=(), *, capacity=NPC_WIDTH):
    if capacity not in (NPC_WIDTH, REFERENCE_WIDTH):
        raise ValueError("Unsupported villager-name capacity")
    source = bank.entries()
    if bank.name != "npc_names" or bank.fixed_size != NPC_WIDTH or len(source) < NPC_COUNT:
        raise ValueError("Unexpected native villager-name layout")
    def indexed(rows):
        result = {}
        for row in rows:
            if row["id"] in result:
                raise ValueError("Duplicate villager-name input ID")
            result[row["id"]] = row
        return result
    inventory, references = indexed(inventory), indexed(references)
    edits, manifests, remaining, counts = [], [], [], Counter()
    for index in range(NPC_COUNT):
        id = f"npc_names:{index:04X}"
        if id in skip_ids:
            counts["original_draft_override"] += 1
            continue
        if id not in inventory or inventory[id].get("source_sha256") != sha256(source[index]):
            raise ValueError("Missing or stale villager-name inventory")
        row, reference = inventory[id], references.get(id)
        reason = None
        if not reference or not reference.get("text"):
            reason = "missing_english_name_reference"
        elif plain(row.get("legacy", "")).strip() != reference["text"]:
            reason = "name_identity_not_confirmed_by_legacy"
        else:
            encoded = encode(reference["text"], info)
            if len(encoded) > REFERENCE_WIDTH or sha256(encoded.ljust(REFERENCE_WIDTH, b" ")) != reference["source_sha256"]:
                raise ValueError("English villager-name reference hash mismatch")
            if any(t.kind != "text" or t.data[0] not in LATIN for t in tokenize(encoded, info)):
                raise ValueError("Villager name must contain only supported plain Latin text")
            if len(encoded) > capacity:
                reason = "full_reference_name_exceeds_native_six_bytes"
        if reason:
            counts["rejected"] += 1
            remaining.append({"id": id, "reason": reason})
            continue
        if capacity == NPC_WIDTH:
            validate_entry(source[index], encoded, info, "npc_names")
        edit = {"id": id, "source_sha256": row["source_sha256"],
                "translation": reference["text"], "control_policy": "exact",
                "provenance": {"source": "user-supplied GAFE01 revision 0 disc",
                               "reference_id": id, "reference_sha256": reference["source_sha256"],
                               "match_basis": "same_id_name_confirmed_by_legacy"},
                "status": "mechanically_validated_candidate_not_reviewed", "adaptations": []}
        edits.append(edit)
        manifest = {k: v for k, v in edit.items() if k != "translation"}
        manifest.update(encoded_bytes=len(encoded), encoded_sha256=sha256(encoded),
                        stored_bytes=capacity, stored_sha256=sha256(encoded.ljust(capacity, b" ")),
                        layout_issues=[], expanded_bound=len(encoded))
        manifests.append(manifest)
        counts["accepted_candidates"] += 1
    report = {**counts, "source_entries": NPC_COUNT, "storage_slots": len(source),
              "excluded_reserve_slots": len(source)-NPC_COUNT,
              "remaining_by_reason": dict(Counter(r["reason"] for r in remaining))}
    return edits, manifests, remaining, report
