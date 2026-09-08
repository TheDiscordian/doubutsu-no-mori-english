#!/usr/bin/env python3
"""Classify every native text record without equating candidates with completion."""

import argparse
from collections import Counter
import json
from pathlib import Path

from aflib import sha256, verified_rom
from runtime_module import module_command_info
from textbanks import banks
from textcodec import GLYPHS, encode, tokenize
from placeholder_text import label


def classify(data, info):
    tokens = list(tokenize(data, info, strict=False))
    visible = "".join(GLYPHS[t.data[0]] for t in tokens if t.kind == "text")
    text = visible.strip()
    kinds = Counter(t.kind for t in tokens)
    if kinds["raw"]:
        category = "undecodable_requires_review"
    elif kinds["glyph"]:
        category = "unmapped_visible_glyph_requires_review"
    elif not text:
        category = "no_visible_static_text"
    elif label(text):
        category = "development_placeholder_text"
    elif any(0x3041 <= ord(c) <= 0x309F or 0x30A1 <= ord(c) <= 0x30FA
             or 0x30FD <= ord(c) <= 0x30FF for c in text):
        category = "japanese_static_text"
    elif any(c.isascii() and c.isalpha() for c in text):
        category = "latin_static_text"
    else:
        category = "numbers_or_symbols_only"
    commands = Counter(f"{t.data[1]:02X}" for t in tokens if t.kind == "cmd")
    return {"category": category, "static_characters": len(text),
            "non_whitespace_static_characters": sum(not c.isspace() for c in text),
            "non_ascii_static_codepoints": sorted({f"U+{ord(c):04X}" for c in text if not c.isascii()}),
            "unmapped_glyphs": kinds["glyph"], "raw_tokens": kinds["raw"],
            "command_counts": dict(sorted(commands.items())),
            "has_dynamic_insertions": any(0x1A <= int(code, 16) <= 0x3F for code in commands)}


def index_edits(edits):
    if not isinstance(edits, list):
        raise ValueError("Candidate edits must be a list")
    result = {}
    for edit in edits:
        if (not isinstance(edit, dict) or not isinstance(edit.get("id"), str)
                or not isinstance(edit.get("translation"), str)):
            raise ValueError("Malformed candidate edit")
        if edit["id"] in result:
            raise ValueError("Duplicate candidate ID")
        result[edit["id"]] = edit
    return result


def coverage_rows(name, entries, edits, info):
    result = []
    for number, source in enumerate(entries):
        id = f"{name}:{number:04X}"
        row = {"id": id, "source_sha256": sha256(source), "source": classify(source, info),
               "candidate_present": id in edits, "review_complete": False,
               "reachability": "not_established", "control_flow_audit_required": name == "message"}
        if id in edits:
            edit = edits[id]
            if edit.get("source_sha256") != row["source_sha256"]:
                raise ValueError(f"Stale candidate source: {id}")
            candidate = encode(edit["translation"], info)
            row.update(candidate_sha256=sha256(candidate), candidate=classify(candidate, info),
                       candidate_status=edit.get("status", "unspecified_requires_review"))
            provenance = edit.get("provenance")
            if isinstance(provenance, dict):
                row["reference"] = {key: provenance[key] for key in
                                    ("reference_id", "reference_sha256", "match_basis") if key in provenance}
            elif isinstance(provenance, str):
                row["provenance_kind"] = "original_edit_description"
        result.append(row)
    return result


def text_volume(rows):
    """Weight Japanese-source records by their visible text, not record count."""
    native = [r for r in rows if r['source']['category'] == 'japanese_static_text']
    english = [r for r in native if r['candidate_present']
               and r['candidate']['category'] in ('latin_static_text', 'numbers_or_symbols_only')
               and r['candidate']['non_whitespace_static_characters'] > 0]
    total = sum(r['source']['non_whitespace_static_characters'] for r in native)
    covered = sum(r['source']['non_whitespace_static_characters'] for r in english)
    return {'japanese_source_records': len(native), 'english_candidate_records': len(english),
            'total_source_characters': total, 'covered_source_characters': covered,
            'coverage_percent': round(100*covered/total, 1) if total else None}


def summarise(rows):
    present = [r for r in rows if r["candidate_present"]]
    absent = [r for r in rows if not r["candidate_present"]]
    return {"native_records": len(rows), "candidate_records": len(present),
            "japanese_text_volume": text_volume(rows),
            "records_without_candidates": len(absent), "review_complete_records": 0,
            "source_categories": dict(sorted(Counter(r["source"]["category"] for r in rows).items())),
            "without_candidate_categories": dict(sorted(Counter(r["source"]["category"] for r in absent).items())),
            "candidate_categories": dict(sorted(Counter(r["candidate"]["category"] for r in present).items())),
            "without_candidate_dynamic_only": sum(r["source"]["category"] == "no_visible_static_text"
                                                  and r["source"]["has_dynamic_insertions"] for r in absent)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--translations", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/coverage"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    raw_edits = args.translations.read_bytes()
    edits = index_edits(json.loads(raw_edits))
    info = module_command_info(rom)
    by_bank = {bank.name: coverage_rows(bank.name, bank.entries(), edits, info) for bank in banks(rom)}
    known = {row["id"] for rows in by_bank.values() for row in rows}
    if edits.keys()-known:
        raise ValueError(f"Unknown candidate IDs: {sorted(edits.keys()-known)}")
    report = {"schema": 1, "rom_sha256": sha256(rom), "translations_sha256": sha256(raw_edits),
              "scope": "29 native banks and ordinary candidate edits; excludes separate wider-name resources and embedded UI/assets",
              "completion_claim": False, "banks": {name: summarise(rows) for name, rows in by_bank.items()}}
    report['japanese_text_volume'] = text_volume([row for rows in by_bank.values() for row in rows])
    report['text_volume_method'] = (
        'Non-whitespace visible source characters in Japanese-static-text records across all 29 native banks. '
        'A decoded Latin or punctuation/symbol candidate covers its complete source character weight, '
        'independently of English length; this includes English letter-header punctuation. '
        'Each native ID is counted separately. Commands, exact development labels, already-Latin records, '
        'symbol-only records, and undecodable records are excluded. '
        'Embedded UI and image text are outside this inventory; separate runtime resources receive no extra credit. '
        'Candidate coverage is not semantic review, complete caller integration, gameplay, or project completion.')
    args.output.mkdir(parents=True, exist_ok=True)
    for name, rows in by_bank.items():
        (args.output/(name+".jsonl")).write_text("".join(json.dumps(r)+"\n" for r in rows))
    (args.output/"summary.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
