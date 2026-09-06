#!/usr/bin/env python3
"""Assert recorded long-choice, name, town-field, and arrival regressions."""

import argparse
import hashlib
import json
from pathlib import Path


def validate(directory):
    results = json.loads((directory/"results.json").read_text())
    rom_hash = hashlib.sha256((directory/"test.z64").read_bytes()).hexdigest()
    if results[0].get("rom_sha256") != rom_hash:
        raise ValueError("Recorded runtime test ROM hash does not match")
    checks = {}
    checks["four_mib"] = any(r.get("read") == ["80000318", 4] and r.get("data") == "00400000"
                             and r.get("assertion") == "passed" for r in results)
    checks["process_survived"] = any(r.get("process_alive") is True for r in results)
    choices = [r for r in results if "choice_lengths" in r]
    checks["sixteen_byte_row"] = any(16 in r["choice_lengths"] for r in choices)
    checks["sixteen_byte_answer_preserved"] = any(
        r["selected_length"] == 16 and len(bytes.fromhex(r["selected_hex"])) == 16
        and r["selected_hex"] in r["choice_hex"] for r in choices)
    checks["three_long_choices"] = any(sum(n > 10 for n in r["choice_lengths"]) >= 3 for r in choices)
    checks["choice_dimensions"] = bool(choices) and all(
        0 <= r["choice_count"] <= 4 and len(r["choice_hex"]) == r["choice_count"]
        and r.get("choice_capacity", 16) in (16, 20)
        and all(len(bytes.fromhex(s)) == n <= r.get("choice_capacity", 16)
                for s, n in zip(r["choice_hex"], r["choice_lengths"]))
        for r in choices)
    for label, value in (("player", "434343434343"), ("town", "414141414141")):
        checks[label+"_six_character_entry"] = any(r.get("text_hex") == value and r.get("length") == 6
                                                  and r.get("columns") == 6 for r in results)
    town_messages = [r for r in results if r.get("message_id") == "2ACE"
                     and "414141414141" in r.get("data", "").lower()]
    checks["town_field_without_japanese_suffix"] = bool(town_messages) and all(
        "414141414141237b" not in r["data"].lower() for r in town_messages)
    checks["arrival_message"] = any(r.get("message_id") == "07DD" for r in results)
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"Runtime smoke acceptance failed: {failed}")
    return {"rom_sha256": rom_hash, "recorded_steps": len(results), "checks": checks,
            "hardware_validation": False, "game_save_reload_validation": False,
            "actor_specific_choice_validation": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    report = validate(args.directory)
    (args.directory/"validation.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
