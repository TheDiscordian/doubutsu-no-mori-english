"""Transfer confirmed placed-object names to proven native lookup aliases."""

from collections import Counter

from aflib import sha256
from textcodec import LATIN, encode, tokenize


def ordinary_item(item):
    """Pinned retail 800BF10C conversion, verified by native loader scenarios."""
    for start, end, base in ((0x17AC, 0x1BA8, 0x2400), (0x1BA8, 0x1C28, 0x2D00),
                              (0x1C28, 0x1CA8, 0x2300), (0x1CA8, 0x1D28, 0x2204)):
        if start <= item < end:
            return base+((item-start) >> 2)
    return item


def confirmed_aliases(source_banks, edits, info, capacity=10, skip_ids=()):
    if capacity not in (10, 16):
        raise ValueError("Unsupported item alias capacity")
    entries = {name: bank.entries() for name, bank in source_banks.items() if name.startswith("item_")}
    indexed = {}
    for edit in edits:
        if edit["id"] in indexed:
            raise ValueError("Duplicate item alias input ID")
        indexed[edit["id"]] = edit
    aliases = {}
    for item in range(0x17AC, 0x1D28):
        donor_id = f"item_10:{item-0x1000:04X}"
        donor = indexed.get(donor_id)
        if donor is None:
            continue
        converted = ordinary_item(item)
        name, index = f"item_{converted >> 8:02X}", converted & 255
        id = f"{name}:{index:04X}"
        if id in skip_ids:
            continue
        original = entries["item_10"][item-0x1000]
        target = entries[name][index]
        if donor["source_sha256"] != sha256(original):
            raise ValueError("Stale item alias donor")
        if original != target:
            continue
        candidate = encode(donor["translation"], info)
        if not candidate or any(t.kind != "text" or t.data[0] not in LATIN for t in tokenize(candidate, info)):
            raise ValueError("Item alias donor must contain complete plain Latin text")
        if len(candidate) > capacity:
            continue
        existing = indexed.get(id) or aliases.get(id)
        if existing:
            if existing["translation"] != donor["translation"]:
                raise ValueError("Conflicting English names for a verified native item alias")
            continue
        provenance = donor.get("provenance")
        if (not isinstance(provenance, dict) or
                provenance.get("reference_sha256") != sha256(candidate.ljust(16, b" "))):
            raise ValueError("Unverified item alias reference")
        aliases[id] = {**donor, "id": id, "source_sha256": sha256(target),
                       "provenance": {**provenance,
                           "match_basis": "native_placed_conversion_and_identical_source_name",
                           "native_equivalent_id": donor_id,
                           "native_item_id": f"{item:04X}", "converted_item_id": f"{converted:04X}"},
                       "adaptations": [{"operation": "use_confirmed_native_item_alias", "donor_id": donor_id}]}
    return list(aliases.values())


def update_alias_reports(edits, aliases, remaining, reports):
    """Keep per-bank remaining files and storage-slot counters consistent."""
    for edit in aliases:
        name = edit["id"].split(":")[0]
        matches = [row for row in remaining[name] if row["id"] == edit["id"]]
        if len(matches) != 1:
            raise ValueError("Item alias is not a unique previously rejected slot")
        remaining[name].remove(matches[0])
        report = reports[name]
        report["accepted_candidates"] = report.get("accepted_candidates", 0)+1
        report["rejected"] -= 1
        report["confirmed_native_aliases"] = report.get("confirmed_native_aliases", 0)+1
        report["remaining_by_reason"] = dict(Counter(row["reason"] for row in remaining[name]))
        report["accepted_reference_identities"] = len({row["provenance"]["reference_id"]
            for row in [*edits, *aliases] if row["id"].startswith(name+":")})
