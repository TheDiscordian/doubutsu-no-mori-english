#!/usr/bin/env python3
"""Build auditable local candidates; never label a mechanical match reviewed."""

import argparse
from collections import Counter
import json
from pathlib import Path

from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from font import make_halfwidth
from gc_text import plain
from textbanks import banks
from textcodec import command_info, encode
from textvalidate import expanded_bound, layout_issues, validate_entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--gc-text", type=Path, default=Path("build/gamecube/text"))
    parser.add_argument("--inventory", type=Path, default=Path("build/inventory"))
    parser.add_argument("--drafts", type=Path, default=Path("translations/opening.json"))
    parser.add_argument("--output", type=Path, default=Path("build/candidates"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    _, font_report = make_halfwidth(rom)
    advances = {int(k, 16): v for k, v in font_report["advance_by_glyph"].items()}
    source_banks = {bank.name: bank for bank in banks(rom)}
    drafts = json.loads(args.drafts.read_text())
    override_ids = {r["id"] for r in drafts}
    edits, manifests, reports = [], [], {}
    for name in ("message", "select"):
        gc = {row["id"]: row for row in map(json.loads, (args.gc_text/(name+".jsonl")).read_text().splitlines())}
        inventory = [json.loads(line) for line in (args.inventory/(name+".jsonl")).read_text().splitlines()]
        source = source_banks[name].entries()
        counts, review = Counter(), []
        for row in inventory:
            id = row["id"]
            if id in override_ids:
                counts["original_draft_override"] += 1
                continue
            reference = gc.get(id)
            reason = None
            if not reference or "text" not in reference:
                reason = "no_same_id_reference"
            elif not plain(reference["text"]) or plain(reference["text"]) != plain(row.get("legacy", "")):
                reason = "same_id_not_confirmed_by_legacy"
            else:
                try:
                    candidate = encode(reference["text"], info)
                    original = source[int(id.split(":")[1], 16)]
                    validate_entry(original, candidate, info, name, "presentation")
                except ValueError as exc:
                    reason = str(exc)
            if reason:
                counts["rejected"] += 1
                review.append({"id": id, "reason": reason})
                continue
            edit = {"id": id, "source_sha256": row["source_sha256"],
                    "translation": reference["text"], "control_policy": "presentation",
                    "provenance": {"source": "user-supplied GAFE01 revision 0 disc",
                                   "reference_id": reference["id"], "reference_sha256": reference["sha256"]},
                    "status": "mechanically_validated_candidate_not_reviewed"}
            issues = layout_issues(candidate, info, advances) if name == "message" else []
            manifest = {k: v for k, v in edit.items() if k != "translation"}
            manifest.update(encoded_sha256=sha256(candidate), encoded_bytes=len(candidate),
                            layout_issues=issues,
                            expanded_bound=expanded_bound(candidate, info) if name == "message" else len(candidate))
            edits.append(edit)
            manifests.append(manifest)
            counts["accepted_candidates"] += 1
            counts["layout_review_required"] += bool(issues)
        reports[name] = dict(counts)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output/(name+"-remaining.jsonl")).write_text("".join(json.dumps(r)+"\n" for r in review))
    edits += drafts
    (args.output/"translations.json").write_text(json.dumps(edits, ensure_ascii=False, indent=2)+"\n")
    (args.output/"manifest.json").write_text(json.dumps(manifests, indent=2)+"\n")
    (args.output/"summary.json").write_text(json.dumps(reports, indent=2)+"\n")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
