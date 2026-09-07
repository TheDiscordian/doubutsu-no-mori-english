"""Reuse unambiguous English candidates for completely identical native records."""

from collections import defaultdict

from aflib import sha256
from gc_adapter import adapt_reference
from textcodec import encode
from textvalidate import validate_entry

POLICIES = {"presentation", "reference_text", "reference_delivery", "reference_layout"}


def confirmed_message_aliases(source, edits, references, info, *, skip_ids=(), resident_runtime=False):
    indexed, by_source = {}, defaultdict(list)
    # CUTARTICLE is removed by the existing audited adapter. It still belongs
    # in the unmodified GameCube reference hash; it is never enabled at runtime.
    reference_info = list(info)+[(0, 0)]*max(0, 0x75-len(info))
    reference_info[0x74] = (2, 0)
    for edit in edits:
        id = edit["id"]
        if not id.startswith("message:"):
            continue
        if id in indexed:
            raise ValueError("Duplicate message alias donor ID")
        indexed[id] = edit
        if id in skip_ids or edit.get("control_policy") not in POLICIES:
            continue
        if edit.get("status") != "mechanically_validated_candidate_not_reviewed":
            continue
        provenance = edit.get("provenance")
        if not isinstance(provenance, dict):
            continue
        number = int(id.split(":")[1], 16)
        if not 0 <= number < len(source) or sha256(source[number]) != edit["source_sha256"]:
            raise ValueError("Stale native message alias donor")
        reference = references.get(provenance.get("reference_id"))
        if (not reference or reference.get("sha256") != provenance.get("reference_sha256")
                or sha256(encode(reference["text"], reference_info)) != reference["sha256"]):
            raise ValueError("Stale message alias English reference")
        expected, _ = adapt_reference(reference["text"], source[number], info,
                                      edit["control_policy"], resident_runtime=resident_runtime)
        candidate = encode(edit["translation"], info)
        if encode(expected, info) != candidate:
            raise ValueError("Message alias donor differs from its complete adapted reference")
        validate_entry(source[number], candidate, info, "message", edit["control_policy"],
                       resident_runtime=resident_runtime)
        by_source[source[number]].append((edit, candidate))
    aliases, conflicts = [], []
    for number, original in enumerate(source):
        id = f"message:{number:04X}"
        if id in indexed or id in skip_ids:
            continue
        donors = by_source.get(original, [])
        if not donors:
            continue
        if len({candidate for _, candidate in donors}) != 1:
            conflicts.append({"id": id, "source_sha256": sha256(original),
                              "reason": "identical_native_records_have_different_english_candidates",
                              "donor_ids": sorted(d["id"] for d, _ in donors)})
            continue
        donor, candidate = min(donors, key=lambda pair: pair[0]["id"])
        validate_entry(original, candidate, info, "message", donor["control_policy"],
                       resident_runtime=resident_runtime)
        aliases.append({**donor, "id": id, "source_sha256": sha256(original),
                        "provenance": {**donor["provenance"],
                            "match_basis": "identical_complete_native_record_and_unanimous_reference_candidate",
                            "native_equivalent_id": donor["id"],
                            "native_equivalent_ids": sorted(d["id"] for d, _ in donors)},
                        "adaptations": [*donor.get("adaptations", []),
                                        {"operation": "use_confirmed_native_message_alias", "donor_id": donor["id"]}]})
    return aliases, conflicts
