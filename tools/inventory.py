#!/usr/bin/env python3
"""Extract editable JSONL and compare the legacy script against Japanese originals."""

import argparse
from collections import Counter
import json
from pathlib import Path

from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from textbanks import banks
from textcodec import command_info, control_signature, decode, encode, has_japanese, tokenize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--legacy", type=Path, default=Path("build/inspect/legacy.z64"))
    parser.add_argument("--output", type=Path, default=Path("build/inventory"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    original = banks(rom)
    legacy = {b.name: b for b in banks(args.legacy.read_bytes(), legacy=True)}
    args.output.mkdir(parents=True, exist_ok=True)
    report = {}
    for bank in original:
        old, legacy_error = bank.entries(), None
        try:
            translated = legacy[bank.name].entries()
        except ValueError as exc:
            translated, legacy_error = [], str(exc)
        legacy_entries = len(translated)
        assert bank.rebuild(old) == (bank.data, bank.table), bank.name
        rows, counts = [], Counter()
        for i, data in enumerate(old):
            text = decode(data, info, strict=False)
            if encode(text, info, allow_raw=True) != data:
                raise ValueError(f"{bank.name}:{i:04X}: codec round trip failed")
            row = {"id": f"{bank.name}:{i:04X}", "source_sha256": sha256(data),
                   "source": text, "source_bytes": len(data), "translation": None,
                   "status": "untranslated"}
            try:
                list(tokenize(data, info))
            except ValueError as exc:
                row["source_error"] = str(exc)
                counts["source_errors"] += 1
            legacy_index = i//4 if bank.name == "item_10" else i
            if legacy_index < len(translated):
                candidate = translated[legacy_index]
                if bank.name.startswith("item_"):
                    row["legacy_entry_id"] = f"{bank.name}:{legacy_index:04X}"
                row["legacy"] = decode(candidate, info, strict=False)
                row["legacy_bytes"] = len(candidate)
                row["legacy_japanese"] = has_japanese(candidate, info)
                row["legacy_same"] = candidate == data
                issues = []
                try:
                    candidate_commands = control_signature(candidate, info)
                    if candidate_commands != control_signature(data, info):
                        issues.append("control_signature_changed")
                except ValueError as exc:
                    issues.append(str(exc))
                if bank.name in ("mail", "maila", "mailb", "mailc") and len(candidate) > 96:
                    issues.append("exceeds_96_byte_mail_body_before_expansion")
                if bank.name == "message" and len(candidate) > 0x400:
                    issues.append("exceeds_1024_byte_message_before_expansion")
                row["legacy_issues"] = issues
                if candidate == data:
                    status = "unchanged"
                elif row["legacy_japanese"]:
                    status = "contains_japanese"
                else:
                    status = "english_candidate_needs_review"
                counts[status] += 1
                counts["legacy_with_issues"] += bool(issues)
            else:
                counts["missing_in_legacy"] += 1
            counts["entries"] += 1
            rows.append(row)
        report[bank.name] = {**dict(counts), "legacy_entries": legacy_entries,
                             "capacity": len(bank.data), "roundtrip": "passed"}
        if legacy_error:
            report[bank.name]["legacy_bank_error"] = legacy_error
        if bank.name.startswith("item_"):
            report[bank.name]["legacy_mapping_status"] = "verified actual loader tables; furniture rotation IDs map four to one"
        (args.output / f"{bank.name}.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
