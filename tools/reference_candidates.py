#!/usr/bin/env python3
"""Build auditable local candidates; never label a mechanical match reviewed."""

import argparse
from collections import Counter
import json
from pathlib import Path

from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from font import make_halfwidth
from gc_adapter import adapt_reference
from textbanks import banks
from textcodec import command_info, encode
from textvalidate import expanded_bound, layout_issues, validate_entry
from runtime_module import add_runtime_module, module_command_info
from reference_matches import load_matches, resolve_reference
from reference_sequences import reference_sequence_edits

REFERENCE_BANKS = ("message", "select", "string", "mail", "super", "ps",
                   "maila", "mailb", "mailc", "psz", "superz")


def load_drafts(paths):
    drafts = []
    for path in paths:
        rows = json.loads(path.read_text())
        if not isinstance(rows, list):
            raise ValueError("Original translations must be a list")
        drafts.extend(rows)
    ids = [row["id"] for row in drafts]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate original translation ID")
    return drafts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--gc-text", type=Path, default=Path("build/gamecube/text"))
    parser.add_argument("--inventory", type=Path, default=Path("build/inventory"))
    parser.add_argument("--drafts", type=Path, action="append", help="Repeat to select explicit original-edit files")
    parser.add_argument("--matches", type=Path, default=Path("translations/reference_matches.json"))
    parser.add_argument("--output", type=Path, default=Path("build/candidates"))
    parser.add_argument("--english-runtime", action="store_true")
    parser.add_argument("--runtime-module", type=Path)
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    choice_bytes = 16 if args.english_runtime else 10
    if args.runtime_module:
        _, module_report = add_runtime_module(rom, {}, args.runtime_module)
        if args.english_runtime:
            choice_bytes = module_report["choice_layout"]["capacity"]
        info = module_command_info(rom)
    _, font_report = make_halfwidth(rom)
    advances = {int(k, 16): v for k, v in font_report["advance_by_glyph"].items()}
    source_banks = {bank.name: bank for bank in banks(rom)}
    drafts = load_drafts(args.drafts or [Path("translations/opening.json"), Path("translations/n64-exercise.json")])
    override_ids = {r["id"] for r in drafts if not r.get("reference_fallback", False)}
    matches = load_matches(args.matches)
    visited_matches = set()
    if override_ids & matches.keys():
        raise ValueError("Reviewed reference match conflicts with an original draft override")
    edits, manifests, reports = [], [], {}
    for name in REFERENCE_BANKS:
        gc = {row["id"]: row for row in map(json.loads, (args.gc_text/(name+".jsonl")).read_text().splitlines())}
        inventory = [json.loads(line) for line in (args.inventory/(name+".jsonl")).read_text().splitlines()]
        source = source_banks[name].entries()
        sequence_edits, permits = reference_sequence_edits(gc, source, info) if name == "message" else ([], {})
        sequences = {edit["id"]: edit for edit in sequence_edits}
        if sequences.keys() & (override_ids | matches.keys()):
            raise ValueError("Reviewed sequence conflicts with a draft or identity override")
        if sequences.keys() - {row["id"] for row in inventory}:
            raise ValueError("Reviewed sequence is absent from the inventory")
        counts, review = Counter(), []
        for row in inventory:
            id = row["id"]
            if id in override_ids:
                counts["original_draft_override"] += 1
                continue
            original = source[int(id.split(":")[1], 16)]
            if id in sequences:
                edit = sequences[id]
                if row["source_sha256"] != edit["source_sha256"]:
                    raise ValueError("Stale sequence inventory")
                text, policy, adaptations = edit["translation"], edit["control_policy"], edit["adaptations"]
                candidate = encode(text, info)
                validate_entry(original, candidate, info, name, policy, choice_bytes=choice_bytes,
                               resident_runtime=bool(args.runtime_module), sequence_permit=permits[id])
            else:
                reference, match_basis, reason = resolve_reference(row, gc, matches, original)
                if id in matches:
                    visited_matches.add(id)
                if reason is None:
                    try:
                        policy = "presentation"
                        try:
                            text, adaptations = adapt_reference(reference["text"], original, info,
                                                                resident_runtime=bool(args.runtime_module))
                            candidate = encode(text, info)
                            validate_entry(original, candidate, info, name, policy,
                                           choice_bytes=choice_bytes,
                                           resident_runtime=bool(args.runtime_module))
                        except ValueError as exc:
                            if name != "message" or str(exc) != "Control signature changed":
                                raise
                            for policy in ("reference_text", "reference_delivery", "reference_layout"):
                                try:
                                    text, adaptations = adapt_reference(reference["text"], original, info, policy,
                                                                        resident_runtime=bool(args.runtime_module))
                                    candidate = encode(text, info)
                                    validate_entry(original, candidate, info, name, policy,
                                                   choice_bytes=choice_bytes,
                                                   resident_runtime=bool(args.runtime_module))
                                    break
                                except ValueError as exc:
                                    if policy == "reference_layout" or str(exc) != "Control signature changed":
                                        raise
                    except ValueError as exc:
                        reason = str(exc)
                if reason:
                    counts["rejected"] += 1
                    review.append({"id": id, "reason": reason})
                    continue
                edit = {"id": id, "source_sha256": row["source_sha256"],
                        "translation": text, "control_policy": policy,
                        "provenance": {"source": "user-supplied GAFE01 revision 0 disc",
                                       "reference_id": reference["id"], "reference_sha256": reference["sha256"],
                                       "match_basis": match_basis},
                        "status": "mechanically_validated_candidate_not_reviewed", "adaptations": adaptations}
            issues = layout_issues(candidate, info, advances) if name == "message" else []
            manifest = {k: v for k, v in edit.items() if k != "translation"}
            manifest.update(encoded_sha256=sha256(candidate), encoded_bytes=len(candidate),
                            layout_issues=issues,
                            expanded_bound=expanded_bound(candidate, info) if name == "message" else len(candidate))
            edits.append(edit)
            manifests.append(manifest)
            counts["accepted_candidates"] += 1
            counts["adapted_candidates"] += bool(adaptations)
            counts["text_field_delivery_candidates"] += policy == "reference_text"
            counts["reference_page_delivery_candidates"] += policy == "reference_delivery"
            counts["reference_layout_candidates"] += policy == "reference_layout"
            counts["reviewed_sequence_candidates"] += policy == "reviewed_sequence"
            counts["layout_review_required"] += bool(issues)
        reports[name] = {**dict(counts), "source_entries": len(source),
                         "remaining_by_reason": dict(Counter(r["reason"] for r in review))}
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output/(name+"-remaining.jsonl")).write_text("".join(json.dumps(r)+"\n" for r in review))
    if matches.keys()-visited_matches:
        raise ValueError(f"Reviewed references are absent from the inventory: {matches.keys()-visited_matches}")
    selected = {edit["id"] for edit in edits}
    edits += [edit for edit in drafts if edit["id"] not in selected]
    (args.output/"translations.json").write_text(json.dumps(edits, ensure_ascii=False, indent=2)+"\n")
    (args.output/"manifest.json").write_text(json.dumps(manifests, indent=2)+"\n")
    (args.output/"summary.json").write_text(json.dumps(reports, indent=2)+"\n")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
