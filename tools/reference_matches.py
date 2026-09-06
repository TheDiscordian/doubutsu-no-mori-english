"""Hash-bound, individually reviewed reference identity overrides."""

import json
import re

from aflib import sha256
from gc_text import plain


def load_matches(path):
    records = json.loads(path.read_text())
    if not isinstance(records, list):
        raise ValueError("Reference matches must be a list")
    result = {}
    for record in records:
        for key in ("id", "reference_id"):
            if not re.fullmatch(r"[a-z_]+:[0-9A-F]{4}", record.get(key, "")):
                raise ValueError("Invalid reviewed reference ID")
        if record["id"].split(":")[0] != record["reference_id"].split(":")[0]:
            raise ValueError("Cross-bank reference matches require a separate audit")
        if "native_equivalent_id" in record:
            equivalent = record["native_equivalent_id"]
            if (not re.fullmatch(r"[a-z_]+:[0-9A-F]{4}", equivalent)
                    or equivalent.split(":")[0] != record["id"].split(":")[0]
                    or equivalent == record["id"]):
                raise ValueError("Invalid native-equivalent reference ID")
        for key in ("source_sha256", "reference_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", record.get(key, "")):
                raise ValueError("Invalid reviewed reference hash")
        if not record.get("evidence", "").strip() or record["id"] in result:
            raise ValueError("Duplicate or unexplained reviewed reference match")
        result[record["id"]] = record
    return result


def verify_native_equivalents(matches, source_banks):
    for match in matches.values():
        if "native_equivalent_id" not in match:
            continue
        name, number = match["native_equivalent_id"].split(":")
        entries = source_banks[name].entries()
        index = int(number, 16)
        if index >= len(entries) or sha256(entries[index]) != match["source_sha256"]:
            raise ValueError("Reviewed native-equivalent record changed")


def resolve_reference(row, references, matches, source):
    match = matches.get(row["id"])
    reference = references.get(match["reference_id"] if match else row["id"])
    if match:
        if (match["source_sha256"] != sha256(source) or row["source_sha256"] != sha256(source)
                or not reference or match["reference_sha256"] != reference.get("sha256")):
            raise ValueError(f"Stale reviewed reference match: {row['id']}")
        if not reference.get("text") or not plain(reference["text"]):
            raise ValueError("Reviewed reference must contain visible text")
        return reference, "reviewed_identity", None
    if not reference or "text" not in reference:
        return None, None, "no_same_id_reference"
    if not plain(reference["text"]) or plain(reference["text"]) != plain(row.get("legacy", "")):
        return None, None, "same_id_not_confirmed_by_legacy"
    return reference, "same_id_confirmed_by_legacy", None
